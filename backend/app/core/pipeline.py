"""5단계 — 전체 analyze 조립 (스펙 4.4).

추출 → 문장분리 → 임베딩 후보검색 → 판정 → 조립.
"""
import uuid

from app.core.embedding import find_candidates
from app.core.extract import extract_requirements
from app.core.judge import judge
from app.core.sentences import split_sentences


def analyze(job_posting: str, cover_letter: str) -> dict:
    # 1) 추출 (Groq 우선, 실패 시 Gemini)
    requirements = extract_requirements(job_posting)
    # 2) 문장 분리
    sentences = split_sentences(cover_letter)
    # 3) 임베딩 + 후보
    candidates = find_candidates(requirements, sentences)
    # 4) 판정 (Gemini 우선, 실패 시 Groq)
    judgments = judge(requirements, candidates)

    # 5) 조립 — id로 추출 결과와 판정 결과 병합
    judge_map = {j["id"]: j for j in judgments}
    merged = []
    for req in requirements:
        j = judge_map.get(req["id"], {})
        merged.append({
            "id": req["id"],
            "text": req["text"],
            "category": req.get("category"),
            "status": j.get("status", "missing"),
            "evidence_ids": j.get("evidence_ids", []),
            "comment": j.get("comment", ""),
            "suggestion": j.get("suggestion"),
        })

    counts = {"met": 0, "weak": 0, "missing": 0}
    for r in merged:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    return {
        "analysis_id": str(uuid.uuid4()),
        "summary": {
            "total": len(merged),
            **counts,
            "coverage_score": round(counts["met"] / len(merged), 2) if merged else 0,
        },
        "cover_letter_sentences": sentences,
        "requirements": merged,
    }
