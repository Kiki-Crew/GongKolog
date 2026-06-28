"""5단계 — analyze_item(문항별) + analyze(문항 루프) 조립 (스펙 v2 3장).

문항 N개 → LLM 2N번 (추출 N + 판정 N).
"""
import uuid

from app.core.embedding import find_candidates
from app.core.extract import extract_categories
from app.core.judge import judge
from app.core.sentences import split_sentences


def analyze_item(item: dict, job_posting: str, item_id: str) -> dict:
    """문항 1개(질문+답변) + 공통 공고 → 카테고리별 충족 판정."""
    # 1) 문항+공고 → 카테고리 추출 (Groq 우선)
    categories = extract_categories(item["question"], job_posting)
    # 2) 답변 문장 분리
    sentences = split_sentences(item["answer"])
    # 3) criteria ↔ 답변 문장 임베딩 후보
    candidates = find_candidates(categories, sentences)
    # 4) 판정 (Gemini 우선)
    judgments = judge(categories, candidates)

    # 5) 조립
    judge_map = {j["id"]: j for j in judgments}
    merged = []
    for c in categories:
        j = judge_map.get(c["id"], {})
        merged.append({
            "id": c["id"],
            "category": c["category"],
            "from": c.get("from", []),
            "criteria": c["criteria"],
            "status": j.get("status", "missing"),
            "evidence_ids": j.get("evidence_ids", []),
            "comment": j.get("comment", ""),
            "suggestion": j.get("suggestion"),
        })

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


def analyze(job_posting: str, items: list[dict]) -> dict:
    item_results = [
        analyze_item(it, job_posting, f"i{i + 1}") for i, it in enumerate(items)
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
