"""5단계 — analyze_item(문항별) + analyze(문항 루프) 조립 (스펙 v2 3장).

문항 N개 → LLM 2N번 (추출 N + 판정 N).
문항별 집중 분석이 카테고리 다양성과 답변 고유 근거 포착에 더 안정적이다.
"""
import uuid

from app.core.embedding import find_candidates
from app.core.extract import extract_categories
from app.core.job_posting import build_job_context
from app.core.judge import judge
from app.core.sentences import split_sentences
from app.core.question_intent import detect_question_intent, validate_categories


_ANSWER_PREVIEW_HINTS = (
    "했습니다",
    "수행",
    "진행",
    "담당",
    "참여",
    "분석",
    "조사",
    "정리",
    "개발",
    "기획",
    "운영",
    "개선",
    "해결",
    "도출",
    "결과",
    "성과",
    "배웠",
    "느꼈",
    "알게",
    "깨달",
    "이를 통해",
    "이를 바탕",
    "협업",
    "문제",
    "신뢰",
)


def _build_answer_preview(
    sentences: list[dict],
    max_chars: int = 1200,
    max_sentences: int = 8,
) -> str:
    """EXTRACT가 사용자 경험의 방향을 알 수 있도록 답변 핵심 문장만 보냄."""
    if not sentences:
        return ""

    selected_indexes: set[int] = set()

    for index, sentence in enumerate(sentences):
        text = (sentence.get("text") or "").strip()
        if not text:
            continue
        if any(hint in text for hint in _ANSWER_PREVIEW_HINTS):
            selected_indexes.add(index)
        if len(selected_indexes) >= max_sentences:
            break

    # 힌트가 적은 답변도 문항 맥락을 잃지 않도록 앞부분을 보강
    index = 0
    while len(selected_indexes) < min(4, len(sentences)) and index < len(sentences):
        selected_indexes.add(index)
        index += 1

    lines: list[str] = []
    current = 0
    for index in sorted(selected_indexes):
        text = (sentences[index].get("text") or "").strip()
        if not text:
            continue

        remaining = max_chars - current
        if remaining <= 0:
            break

        line = f"- {text}"
        if len(line) > remaining:
            line = line[: max(0, remaining - 3)].rstrip() + "..."

        lines.append(line)
        current += len(line) + 1

    return "\n".join(lines)


def _normalize_category(c: dict, j: dict, valid_sentence_ids: set[str]) -> dict:
    """카테고리 판정 보정"""
    required_evidence = c.get("required_evidence", [])
    checks = j.get("condition_checks") or []

    normalized_checks = []
    fulfilled_count = 0
    evidence_set: set[str] = set()
    evidence_terms: list[str] = []

    for check in checks:
        condition = (check.get("condition") or "").strip()
        fulfilled = bool(check.get("fulfilled"))

        check_evidence_ids = [
            sid for sid in (check.get("evidence_ids") or [])
            if sid in valid_sentence_ids
        ]

        # 근거 문장 없는 fulfilled는 인정하지 않음
        if fulfilled and not check_evidence_ids:
            fulfilled = False

        check_terms = [
            term.strip()
            for term in (check.get("evidence_terms") or [])
            if isinstance(term, str) and term.strip()
        ][:4]

        if fulfilled:
            fulfilled_count += 1
            evidence_set.update(check_evidence_ids)
            evidence_terms.extend(check_terms)

        normalized_checks.append(
            {
                "condition": condition,
                "fulfilled": fulfilled,
                "evidence_ids": check_evidence_ids,
                "evidence_terms": check_terms,
                "reason": (check.get("reason") or "").strip(),
            }
        )

    total_required = len(required_evidence) or len(checks)

    evidence = sorted(
        evidence_set,
        key=lambda sid: int(sid[1:]) if sid.startswith("s") and sid[1:].isdigit() else 999,
    )

    # evidence_terms 중복 제거
    deduped_terms = []
    seen_terms = set()
    for term in evidence_terms:
        if term not in seen_terms:
            deduped_terms.append(term)
            seen_terms.add(term)
    evidence_terms = deduped_terms[:4]

    # status 계산
    if total_required == 0:
        status = "missing" if not evidence else "weak"
    elif fulfilled_count == 0:
        status = "missing"
    elif fulfilled_count >= total_required:
        status = "met"
    else:
        status = "weak"

    comment = (j.get("comment") or "").strip()
    analysis = (j.get("analysis") or "").strip()
    suggestion = (j.get("suggestion") or "").strip() or None

    if status == "met":
        suggestion = None
        comment = comment or "기준을 충족하는 근거가 확인됩니다."
        analysis = analysis or _build_evidence_analysis(
            category_name=c["category"],
            status=status,
            evidence_terms=evidence_terms,
            fallback_analysis="답변의 근거가 평가 기준과 연결됩니다.",
        )

    elif status == "weak":
        comment = comment or "관련 내용은 있으나 근거가 일부 부족합니다."
        analysis = analysis or _build_evidence_analysis(
            category_name=c["category"],
            status=status,
            evidence_terms=evidence_terms,
            fallback_analysis="관련 근거는 있으나 평가 기준을 충분히 설명하기에는 일부 연결이 부족합니다.",
        )
        suggestion = suggestion or "현재 답변의 구체 표현을 기준에 맞게 한 단계 더 연결하면 좋겠습니다."

    else:
        evidence = []
        evidence_terms = []
        comment = comment or "답변에서 이 기준에 해당하는 내용을 찾지 못했습니다."
        analysis = analysis or "이 카테고리를 판단할 수 있는 직접적인 경험, 행동, 결과 근거가 부족합니다."
        suggestion = suggestion or "이 기준을 충족하는 내용을 답변 안에서 구체적으로 보완하면 좋겠습니다."

    if _is_generic_comment(comment):
        comment = _build_evidence_comment(
            category_name=c["category"],
            status=status,
            evidence_terms=evidence_terms,
            fallback_comment=comment,
        )

    return {
        "id": c["id"],
        "category": c["category"],
        "from": c.get("from", []),
        "criteria": c["criteria"],
        "status": status,
        "evidence_ids": evidence,
        "evidence_terms": evidence_terms,
        "comment": comment,
        "analysis": analysis,
        "suggestion": suggestion,
        "condition_checks": normalized_checks,
    }


def _build_item_result(
    item: dict,
    item_id: str,
    categories: list[dict],
    sentences: list[dict],
    judgments: list[dict],
) -> dict:
    judge_map = {j["id"]: j for j in judgments if isinstance(j, dict) and "id" in j}
    valid_sentence_ids = {sentence["id"] for sentence in sentences}

    merged = []
    for c in categories:
        j = judge_map.get(c["id"], {})
        merged.append(_normalize_category(c, j, valid_sentence_ids))

    counts = {"met": 0, "weak": 0, "missing": 0}
    for r in merged:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    return {
        "item_id": item_id,
        "question": item["question"],
        "answer_sentences": sentences,
        "summary": {"total": len(merged), **counts},
        "categories": merged,
    }


def analyze_item(
    item: dict,
    job_posting: str,
    item_id: str,
    categories: list[dict] | None = None,
) -> dict:
    """문항 1개 분석
    1. 정형 문항이면 extract_categories를 호출하지 않음
    2. 짧은 답변이면 embedding 후보 검색을 생략하고 전체 문장으로 judge
    """
    sentences = split_sentences(item["answer"])
    intent = detect_question_intent(item["question"], job_posting)

    if categories is None:
        if intent["use_template"]:
            categories = intent["categories"]
        else:
            categories = extract_categories(
                item["question"],
                job_posting,
                answer_preview=_build_answer_preview(sentences),
            )
    categories = validate_categories(categories, intent)

    if _should_use_full_answer(sentences, item["answer"]):
        judgments = judge(
            categories=categories,
            candidates={},
            answer_sentences=sentences,
            question=item["question"],
            intent_type=intent["type"],
        )
    else:
        candidates = find_candidates(categories, sentences, top_k=3)
        judgments = judge(
            categories=categories,
            candidates=candidates,
            question=item["question"],
            intent_type=intent["type"],
        )
    return _build_item_result(item, item_id, categories, sentences, judgments)


def analyze(job_posting: str, items: list[dict]) -> dict:
    job_context = build_job_context(job_posting, item_count=len(items))
    item_results = [
        analyze_item(it, job_context, f"i{i + 1}") for i, it in enumerate(items)
    ]

    agg = {"met": 0, "weak": 0, "missing": 0}
    total_cat = 0
    for r in item_results:
        for k in agg:
            agg[k] += r["summary"][k]
        total_cat += r["summary"]["total"]

    return {
        "analysis_id": str(uuid.uuid4()),
        "overall_summary": {
            "total_items": len(item_results),
            "total_categories": total_cat,
            **agg,
            "coverage_score": round(agg["met"] / total_cat, 2) if total_cat else 0,
        },
        "items": item_results,
    }

def _should_use_full_answer(sentences: list[dict], answer: str) -> bool:
    """전체 답변 판정 기준"""
    return len(sentences) <= 14 or len(answer) <= 1500

def _is_generic_comment(comment: str) -> bool:
    """일반적인 평가문 여부 판단"""
    generic_phrases = (
        "구체적으로 확인됩니다",
        "구체적으로 제시됩니다",
        "논리적으로 연결됩니다",
        "명확히 제시됩니다",
        "충분히 확인됩니다",
        "잘 드러납니다",
    )

    return any(phrase in comment for phrase in generic_phrases) and len(comment) < 80


def _build_evidence_comment(
    category_name: str,
    status: str,
    evidence_terms: list[str],
    fallback_comment: str,
) -> str:
    """근거 표현 기반 comment 보정"""
    terms = [term.strip() for term in evidence_terms if term and term.strip()]
    terms = terms[:3]

    if not terms:
        return fallback_comment

    term_text = ", ".join(terms)

    if status == "met":
        return f"주요 근거는 {term_text}입니다. 이를 바탕으로 {category_name} 기준을 뒷받침합니다."

    if status == "weak":
        return f"주요 근거는 {term_text}입니다. 다만 {category_name} 기준을 충분히 설명하기에는 일부 연결이 부족합니다."

    return fallback_comment

def _build_evidence_analysis(
    category_name: str,
    status: str,
    evidence_terms: list[str],
    fallback_analysis: str,
) -> str:
    """근거 표현 기반 상세 분석"""
    terms = [term.strip() for term in evidence_terms if term and term.strip()]
    terms = terms[:4]

    if not terms:
        return fallback_analysis

    term_text = ", ".join(terms)

    if status == "met":
        return (
            f"답변의 주요 근거는 {term_text}입니다. "
            f"이 근거들은 단순한 주장보다 실제 경험, 행동, 결과를 함께 보여주기 때문에 "
            f"{category_name} 기준을 설득력 있게 뒷받침합니다."
        )

    if status == "weak":
        return (
            f"답변의 주요 근거는 {term_text}입니다. "
            f"다만 이 근거가 {category_name} 기준과 어떻게 연결되는지에 대한 설명이 일부 부족해 "
            f"평가자가 추가로 추론해야 할 여지가 있습니다."
        )

    return fallback_analysis