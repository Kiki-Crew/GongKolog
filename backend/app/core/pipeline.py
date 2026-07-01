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


_ANSWER_PREVIEW_HINTS = (
    "했습니다",
    "수행",
    "진행",
    "분석",
    "개발",
    "기획",
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
    "활용",
    "적용",
    "기여",
    "입사 후",
    "직무",
    "업무",
    "고객",
    "사용자",
    "협업",
    "문제",
    "신뢰",
)


def _build_answer_preview(
    sentences: list[dict],
    max_chars: int = 1200,
    max_sentences: int = 8,
) -> str:
    """EXTRACT가 사용자 경험의 방향을 알 수 있도록 답변 핵심 문장만 보냅니다."""
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

    # 힌트가 적은 답변도 문항 맥락을 잃지 않도록 앞부분을 보강합니다.
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


def _normalize_category(c: dict, j: dict) -> dict:
    """카테고리 + 판정 → 스펙 status 규칙을 보장

    판정이 비었거나(LLM 빈 응답/형식 오류) 필드가 누락돼도
    met→suggestion null / weak·missing→suggestion 존재 / missing→evidence []
    불변식을 항상 만족하도록 기본값을 채움
    """
    status = j.get("status") or "missing"
    if status not in ("met", "weak", "missing"):
        status = "missing"
    evidence = j.get("evidence_ids") or []
    comment = (j.get("comment") or "").strip()
    suggestion = (j.get("suggestion") or "").strip() or None

    if status == "met":
        suggestion = None
        comment = comment or "기준을 충족하는 근거가 확인됩니다."
    elif status == "weak":
        comment = comment or "관련 내용은 있으나 근거가 약합니다."
        suggestion = suggestion or "기준에 맞는 구체적 사례와 본인 기여를 보강하세요."
    else:  # missing
        evidence = []
        comment = comment or "답변에서 이 기준에 해당하는 내용을 찾지 못했습니다."
        suggestion = suggestion or "이 기준을 충족하는 경험을 답변에 구체적으로 추가하세요."

    return {
        "id": c["id"],
        "category": c["category"],
        "from": c.get("from", []),
        "criteria": c["criteria"],
        "status": status,
        "evidence_ids": evidence,
        "comment": comment,
        "suggestion": suggestion,
    }


def _build_item_result(
    item: dict,
    item_id: str,
    categories: list[dict],
    sentences: list[dict],
    judgments: list[dict],
) -> dict:
    judge_map = {j["id"]: j for j in judgments if isinstance(j, dict) and "id" in j}
    merged = []
    for c in categories:
        j = judge_map.get(c["id"], {})
        merged.append(_normalize_category(c, j))

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
    """문항 1개(질문+답변) + 공통 공고 → 카테고리별 충족 판정"""
    # 1) 답변 문장 분리
    sentences = split_sentences(item["answer"])

    # 2) 문항+공고+답변 미리보기 → 카테고리 추출
    if categories is None:
        categories = extract_categories(
            item["question"],
            job_posting,
            answer_preview=_build_answer_preview(sentences),
        )
    # 3) 카테고리 ↔ 답변 문장 윈도우 임베딩 후보
    candidates = find_candidates(categories, sentences, top_k=4)
    # 4) 판정 (Groq judge 모델)
    judgments = judge(categories, candidates)

    # 5) 조립 — 판정이 비거나 형식이 어긋나도 스펙 불변식을 강제 (데모 안정성)
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
