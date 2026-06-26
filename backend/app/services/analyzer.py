"""분석 파이프라인 조립 (스펙 4.4 2·4·5단계)."""
import json
import uuid

import kss

from app.services.embedding import find_candidates
from app.services.llm import call_with_fallback
from app.services.prompts import EXTRACT_PROMPT, JUDGE_PROMPT


def safe_json(text: str):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def safe_json_retry(prompt: str, primary: str, backup: str):
    """JSON 파싱 실패 시 1회 재시도 (스펙 4.5)."""
    try:
        return safe_json(call_with_fallback(prompt, primary, backup))
    except (json.JSONDecodeError, ValueError):
        return safe_json(call_with_fallback(prompt, primary, backup))


# ── 2단계: 한국어 문장 분리 + id 부여 ──────────────────────────────
def split_sentences(cover_letter: str) -> list[dict]:
    sentences = kss.split_sentences(cover_letter)
    return [
        {"id": f"s{i + 1}", "text": s.strip()}
        for i, s in enumerate(sentences)
        if s.strip()
    ]


# ── 4단계: 판정 입력 빌더 ──────────────────────────────────────────
def build_judge_input(requirements: list[dict], candidates: dict) -> str:
    blocks = []
    for req in requirements:
        cand = candidates[req["id"]]
        lines = [f'요구사항 {req["id"]}: {req["text"]}']
        if cand:
            lines.append("후보 문장:")
            for c in cand:
                s = c["sentence"]
                lines.append(f'  - {s["id"]}: {s["text"]}')
        else:
            lines.append("후보 문장: 없음")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


# ── 5단계: 전체 analyze ────────────────────────────────────────────
def analyze(job_posting: str, cover_letter: str) -> dict:
    # 1) 추출 (Groq 우선, 실패 시 Gemini)
    requirements = safe_json_retry(
        EXTRACT_PROMPT.format(job_posting=job_posting),
        primary="groq", backup="gemini",
    )
    # 2) 문장 분리
    sentences = split_sentences(cover_letter)
    # 3) 임베딩 + 후보
    candidates = find_candidates(requirements, sentences)
    # 4) 판정 (Gemini 우선, 실패 시 Groq)
    judgments = safe_json_retry(
        JUDGE_PROMPT.format(judge_input=build_judge_input(requirements, candidates)),
        primary="gemini", backup="groq",
    )
    # 5) 조립
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
