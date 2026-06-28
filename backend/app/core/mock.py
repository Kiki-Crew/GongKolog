"""Mock 엔진 — 키/모델 없이 파이프라인을 끝까지 돌리기 위한 규칙 기반 대체 (스펙 v2).

순수 stdlib만 사용 (google-genai / openai / sentence-transformers / numpy 불필요).
실제 LLM 품질을 흉내내지는 않지만, **응답 스키마와 단계 연결이 올바른지** 검증하는 용도.
실서비스는 settings.mock_llm / mock_embedding 를 false 로.
"""
import re

_BULLET = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s*")
# 제목/머리말로 보이는 줄은 카테고리에서 제외
_HEADER = re.compile(r"^\[.*\]|채용\s*공고|모집\s*요강|담당\s*업무\s*[:：]?$")


# ── 추출 mock (문항+공고 → 카테고리) ───────────────────────────────
def mock_extract_categories(question: str, job_posting: str, max_items: int = 5) -> list[dict]:
    """문항 1개 + 공고 줄 단위로 평가 카테고리 후보 생성 (규칙 기반)."""
    cats: list[dict] = []

    # 문항 기반 카테고리 1개
    q = question.strip().rstrip("?？").strip()
    cats.append({
        "id": "c1",
        "category": (q[:18] or "문항 요구사항"),
        "from": ["문항"],
        "criteria": q or "문항이 요구하는 내용을 구체적으로 보여줘야 함",
    })

    # 공고 기반 카테고리 (줄/불릿 단위)
    seen = {cats[0]["criteria"]}
    for line in re.split(r"[\n,·]", job_posting):
        text = _BULLET.sub("", line).strip(" .·-")
        if len(text) < 4 or text in seen or _HEADER.search(text):
            continue
        seen.add(text)
        cats.append({
            "id": f"c{len(cats) + 1}",
            "category": text[:18],
            "from": ["공고"],
            "criteria": text,
        })
        if len(cats) >= max_items:
            break
    return cats


# ── 유사도 mock (BGE-M3 대체) ──────────────────────────────────────
def _ngrams(text: str, n: int = 2) -> set[str]:
    t = re.sub(r"\s+", "", text)
    return {t[i:i + n] for i in range(len(t) - n + 1)} if len(t) >= n else {t}


def _jaccard(a: str, b: str) -> float:
    ga, gb = _ngrams(a), _ngrams(b)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    union = len(ga | gb)
    return inter / union if union else 0.0


def mock_find_candidates(categories: list[dict], sentences: list[dict], top_k: int = 3) -> dict:
    if not sentences:
        return {c["id"]: [] for c in categories}
    candidates: dict = {}
    for c in categories:
        scored = sorted(
            (
                {"sentence": s, "score": _jaccard(c["criteria"], s["text"])}
                for s in sentences
            ),
            key=lambda x: x["score"],
            reverse=True,
        )
        candidates[c["id"]] = scored[:top_k]
    return candidates


# ── 판정 mock (유사도 임계값 기반) ─────────────────────────────────
_MET_THRESHOLD = 0.12
_WEAK_THRESHOLD = 0.04


def mock_judge(categories: list[dict], candidates: dict) -> list[dict]:
    out: list[dict] = []
    for c in categories:
        cand = candidates.get(c["id"], [])
        top = cand[0] if cand else None
        score = top["score"] if top else 0.0

        if score >= _MET_THRESHOLD:
            out.append({
                "id": c["id"],
                "status": "met",
                "evidence_ids": [top["sentence"]["id"]],
                "comment": "기준과 답변 문장이 충분히 일치합니다. (mock)",
                "suggestion": None,
            })
        elif score >= _WEAK_THRESHOLD:
            out.append({
                "id": c["id"],
                "status": "weak",
                "evidence_ids": [top["sentence"]["id"]],
                "comment": "관련 언급은 있으나 근거가 약합니다. (mock)",
                "suggestion": "기준에 맞는 구체적 사례나 본인 기여를 한 문장 보강하세요. (mock)",
            })
        else:
            out.append({
                "id": c["id"],
                "status": "missing",
                "evidence_ids": [],
                "comment": "답변에서 기준에 해당하는 내용을 찾지 못했습니다. (mock)",
                "suggestion": "이 기준을 충족하는 경험을 답변에 추가하세요. (mock)",
            })
    return out
