"""5단계 — analyze_item(문항별) + analyze(문항 루프) 조립 (스펙 v2 3장).

문항 N개 → LLM 3N번 (추출 N + 판정 N + 공고 정합성 게이트 N).
문항별 집중 분석이 카테고리 다양성과 답변 고유 근거 포착에 더 안정적이다.
"""
import re
import uuid

from app.core.embedding import find_candidates
from app.core.extract import extract_categories
from app.core.job_fit import ALIGNMENT_MISMATCH, check_job_fit
from app.core.job_posting import build_job_context
# _is_job_required_category: judge 입력 빌더와 게이트가 같은 기준을 공유하기 위해 재사용
from app.core.judge import _is_job_required_category, judge
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

    # condition_checks는 status 계산(충족 수·근거 집계)에만 쓰고 응답에는 내보내지 않는다
    fulfilled_count = 0
    evidence_set: set[str] = set()
    evidence_terms: list[str] = []

    for check in checks:
        fulfilled = bool(check.get("fulfilled"))

        check_evidence_ids = [
            sid for sid in (check.get("evidence_ids") or [])
            if sid in valid_sentence_ids
        ]

        # 근거 문장 없는 fulfilled는 인정하지 않음
        if fulfilled and not check_evidence_ids:
            fulfilled = False

        if fulfilled:
            fulfilled_count += 1
            evidence_set.update(check_evidence_ids)
            evidence_terms.extend(
                term.strip()
                for term in (check.get("evidence_terms") or [])
                if isinstance(term, str) and term.strip()
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

    llm_comment = (j.get("comment") or "").strip()
    analysis = (j.get("analysis") or "").strip()
    suggestion = (j.get("suggestion") or "").strip() or None

    if status == "met":
        analysis = analysis or _build_evidence_analysis(
            category_name=c["category"],
            status=status,
            evidence_terms=evidence_terms,
            fallback_analysis=llm_comment or "답변의 근거가 평가 기준과 연결됩니다.",
        )

    elif status == "weak":
        analysis = analysis or _build_evidence_analysis(
            category_name=c["category"],
            status=status,
            evidence_terms=evidence_terms,
            fallback_analysis=llm_comment or "관련 근거는 있으나 평가 기준을 충분히 설명하기에는 일부 연결이 부족합니다.",
        )
        suggestion = suggestion or f"현재 답변에서 확인되는 경험이 {c['category']} 기준과 어떻게 연결되는지 한 문장 더 보완하면 좋겠습니다."

    else:
        evidence = []
        evidence_terms = []
        analysis = analysis or llm_comment or "이 카테고리를 판단할 수 있는 직접적인 경험, 행동, 결과 근거가 부족합니다."
        suggestion = suggestion or f"{c['category']} 기준을 판단할 수 있는 경험, 행동, 결과 근거를 답변 안에서 구체적으로 보완하면 좋겠습니다."

    # 프론트 Category 계약:
    #   comment    = 상세 분석 2~3문장
    #   suggestion = LLM 보완 제안 1문장
    # condition_checks / evidence_terms / llm_comment는 내부 판정용으로만 사용
    cleaned_analysis = _clean_user_text(analysis) or "분석 내용을 생성하지 못했습니다."
    cleaned_suggestion = _clean_user_text(suggestion)

    return {
        "id": c["id"],
        "category": c["category"],
        "from": c.get("from", []),
        "criteria": c["criteria"],
        "status": status,
        "evidence_ids": evidence,
        "comment": _quote_evidence_terms_in_text(cleaned_analysis, evidence_terms),
        "suggestion": _quote_evidence_terms_in_text(cleaned_suggestion, evidence_terms),
    }


_SENTENCE_ID_PATTERN = re.compile(
    r"[\[(]?\s*s\d+\s*[\])]?:?\s*(?:문장)?(?:에서|에서는|에는|은|는|의|을|를)?"
)

_DIRECTIVE_REPLACEMENTS = (
    ("구체적으로 서술해 보세요", "구체적으로 서술하면 좋겠습니다"),
    ("서술해 보세요", "서술하면 좋겠습니다"),
    ("제시해 보세요", "제시하면 좋겠습니다"),
    ("강조해 보세요", "강조하면 좋겠습니다"),
    ("연결해 보세요", "연결하면 좋겠습니다"),
    ("작성해 보세요", "작성하면 좋겠습니다"),
    ("보완해 보세요", "보완하면 좋겠습니다"),
    ("구체화해 보세요", "구체화하면 좋겠습니다"),
    ("덧붙여 보세요", "덧붙이면 좋겠습니다"),
    ("추가해 보세요", "덧붙이면 좋겠습니다"),
    ("말해 보세요", "설명하면 좋겠습니다"),
    ("밝혀 보세요", "밝히면 좋겠습니다"),
)


def _clean_user_text(text: str | None) -> str | None:
    """사용자 표시 문구 정리"""
    if not text:
        return None

    cleaned = _SENTENCE_ID_PATTERN.sub("", text)
    for before, after in _DIRECTIVE_REPLACEMENTS:
        cleaned = cleaned.replace(before, after)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
    return cleaned.strip() or None

def _quote_term(term: str) -> str:
    """직접 인용 표시"""
    cleaned = term.strip().strip('"“”‘’')
    return f'"{cleaned}"'


def _format_quoted_terms(evidence_terms: list[str], limit: int = 3) -> str:
    """근거 표현을 큰따옴표 인용으로 변환"""
    terms: list[str] = []
    seen: set[str] = set()

    for term in evidence_terms:
        cleaned = re.sub(r"\s+", " ", str(term or "").strip().strip('"“”‘’'))
        if not cleaned or cleaned in seen:
            continue
        terms.append(_quote_term(cleaned))
        seen.add(cleaned)
        if len(terms) >= limit:
            break

    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return ", ".join(terms)


def _quote_evidence_terms_in_text(text: str | None, evidence_terms: list[str]) -> str | None:
    """LLM 문구 안의 직접 근거 표현에 큰따옴표 보강"""
    if not text:
        return None

    result = text
    for term in sorted(evidence_terms, key=len, reverse=True):
        cleaned = re.sub(r"\s+", " ", str(term or "").strip().strip('"“”‘’'))

        # 너무 짧은 단어까지 강제 인용하면 조사 결합이 어색해진다
        if len(cleaned) < 6 and " " not in cleaned:
            continue
        if not cleaned or _quote_term(cleaned) in result:
            continue
        if cleaned in result:
            result = result.replace(cleaned, _quote_term(cleaned), 1)

    return result


def _apply_job_fit_gate(
    merged: list[dict],
    categories: list[dict],
    job_fit: dict | None,
) -> list[dict]:
    """공고-답변 미스매치 시 카테고리 판정을 강등하는 게이트.

    다른 직무·산업의 공고에 자소서를 잘못 넣은 경우 met이 뜨지 않게 한다.
    응답 스키마는 원본 그대로이므로, 게이트 결과는 별도 필드가 아니라
    status 강등과 comment/suggestion 문구로만 표현된다.

    강등 규칙 (mismatch일 때만):
    - 직무 연결이 핵심인 카테고리(지원동기·직무적용류) → missing
      : 잘못된 공고 기준으로는 직무 연결 자체가 성립하지 않음
    - 그 외 카테고리의 met → weak
      : 경험 자체의 구체성은 인정하되, 이 공고 기준의 '충족'으로는 표시하지 않음
    - weak/missing은 그대로 둔다 (이중 감점 방지)

    partial/aligned/unknown이면 판정을 건드리지 않는다.
    전이 가능한 경험(예: 카페 알바 협업 → 사무직 협업 문항)을 보호하기 위해
    게이트는 명백한 충돌에만 작동한다.
    """
    if not job_fit or job_fit.get("alignment") != ALIGNMENT_MISMATCH:
        return merged

    reason = (job_fit.get("reason") or "").strip()
    gate_note = "답변이 대상으로 삼은 직무·산업이 입력된 채용공고와 일치하지 않습니다."
    if reason:
        gate_note = f"{gate_note} {reason}"

    category_map = {c["id"]: c for c in categories}

    for result in merged:
        original = category_map.get(result["id"], result)
        job_required = _is_job_required_category(original)

        if job_required and result["status"] in ("met", "weak"):
            # 직무 연결 카테고리는 잘못된 공고 기준으로 충족될 수 없음
            result["status"] = "missing"
            result["evidence_ids"] = []
            result["comment"] = gate_note[:120]
            result["suggestion"] = (
                f"{gate_note} 지원하려는 직무의 채용공고가 맞는지 확인한 뒤 "
                "다시 분석해 주세요."
            )

        elif result["status"] == "met":
            # 경험 자체는 인정하되 '이 공고 충족'으로는 표시하지 않음
            result["status"] = "weak"
            result["comment"] = f"{result['comment']} (단, 공고와 지원 대상이 다릅니다.)"[:160]
            base = (result["suggestion"] or "").strip()
            result["suggestion"] = " ".join(
                part for part in (
                    base,
                    f"다만 {gate_note} 입력한 채용공고가 지원 직무와 맞는지 확인해 주세요.",
                ) if part
            )

    return merged


def _build_item_result(
    item: dict,
    item_id: str,
    categories: list[dict],
    sentences: list[dict],
    judgments: list[dict],
    job_fit: dict | None = None,
) -> dict:
    judge_map = {j["id"]: j for j in judgments if isinstance(j, dict) and "id" in j}
    valid_sentence_ids = {sentence["id"] for sentence in sentences}

    merged = []
    for c in categories:
        j = judge_map.get(c["id"], {})
        merged.append(_normalize_category(c, j, valid_sentence_ids))

    # 게이트는 카운트 집계 전에 적용해야 summary와 status가 일치한다
    merged = _apply_job_fit_gate(merged, categories, job_fit)

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

    # 답변 미리보기는 EXTRACT와 job_fit 게이트가 공유한다 (중복 생성 방지)
    answer_preview = _build_answer_preview(sentences)

    if categories is None:
        if intent["use_template"]:
            categories = intent["categories"]
        else:
            categories = extract_categories(
                item["question"],
                job_posting,
                answer_preview=answer_preview,
            )
    categories = validate_categories(categories, intent)

    # 공고-답변 정합성 게이트 (문항당 LLM 1회 추가: 2N → 3N)
    # 다른 직무/산업 공고에 잘못 넣은 자소서가 met으로 판정되는 것을 막는다
    job_fit = check_job_fit(
        job_context=job_posting,
        question=item["question"],
        answer_preview=answer_preview,
    )

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
    return _build_item_result(
        item, item_id, categories, sentences, judgments, job_fit=job_fit
    )


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
    term_text = _format_quoted_terms(evidence_terms)

    if not term_text:
        return fallback_comment

    if status == "met":
        return f"{term_text}에서 확인되는 경험과 행동이 {category_name} 기준을 뒷받침합니다."

    if status == "weak":
        return f"{term_text}에서 관련 경험은 확인되지만, {category_name} 기준과의 연결 설명은 일부 부족합니다."

    return fallback_comment

def _build_evidence_analysis(
    category_name: str,
    status: str,
    evidence_terms: list[str],
    fallback_analysis: str,
) -> str:
    """근거 표현 기반 상세 분석"""
    term_text = _format_quoted_terms(evidence_terms, limit=3)

    if not term_text:
        return fallback_analysis

    if status == "met":
        return (
            f"{term_text} 같은 표현에서 지원자의 역할, 실행 과정, 결과가 함께 드러납니다. "
            f"이 내용이 {category_name} 기준에서 요구하는 구체성과 설득력으로 이어지기 때문에, "
            f"평가자가 실제 경험에 기반한 강점으로 읽을 수 있습니다."
        )

    if status == "weak":
        return (
            f"{term_text} 같은 표현에서 관련 경험의 방향은 확인됩니다. "
            f"다만 이 경험이 {category_name} 기준과 어떤 판단, 성과, 업무 전이로 이어지는지가 아직 압축적으로 제시되어 "
            f"평가자가 일부 의미를 추론해야 하는 점은 보완이 필요합니다."
        )

    return fallback_analysis
