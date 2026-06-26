"""Mock 엔진 — 키/모델 없이 파이프라인을 끝까지 돌리기 위한 규칙 기반 대체 (스펙 8장 Tier 1).

순수 stdlib만 사용 (google-genai / openai / sentence-transformers / numpy 불필요).
실제 LLM 품질을 흉내내지는 않지만, **응답 스키마와 단계 연결이 올바른지** 검증하는 용도.
실서비스는 settings.mock_llm / mock_embedding 를 false 로.
"""
import re

# ── 추출 mock ──────────────────────────────────────────────────────
_BULLET = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s*")
_CATEGORY_HINTS = [
    ("기술역량", ["개발", "프로그래밍", "언어", "프레임워크", "DB", "데이터", "코드", "SQL", "API"]),
    ("자격요건", ["학위", "전공", "자격증", "경력", "년 이상", "필수", "우대"]),
    ("인성역량", ["리더십", "소통", "협업", "책임감", "열정", "팀워크"]),
]


def _guess_category(text: str) -> str:
    for cat, kws in _CATEGORY_HINTS:
        if any(k in text for k in kws):
            return cat
    return "경험"


# 제목/머리말로 보이는 줄은 요구사항에서 제외
_HEADER = re.compile(r"^\[.*\]|채용\s*공고|모집\s*요강|담당\s*업무\s*[:：]?$")


def mock_extract(job_posting: str, max_items: int = 8) -> list[dict]:
    """공고를 줄/불릿 단위로 쪼개 요구사항 후보로 (규칙 기반)."""
    lines = re.split(r"[\n,·]", job_posting)
    items: list[dict] = []
    seen: set[str] = set()
    for line in lines:
        text = _BULLET.sub("", line).strip(" .·-")
        if len(text) < 4 or text in seen or _HEADER.search(text):
            continue
        seen.add(text)
        items.append({
            "id": f"r{len(items) + 1}",
            "text": text,
            "category": _guess_category(text),
        })
        if len(items) >= max_items:
            break
    # 아무것도 못 뽑으면 통째로 1개
    if not items:
        items.append({"id": "r1", "text": job_posting.strip()[:60], "category": "경험"})
    return items


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


def mock_find_candidates(requirements: list[dict], sentences: list[dict], top_k: int = 3) -> dict:
    if not sentences:
        return {r["id"]: [] for r in requirements}
    candidates: dict = {}
    for req in requirements:
        scored = sorted(
            (
                {"sentence": s, "score": _jaccard(req["text"], s["text"])}
                for s in sentences
            ),
            key=lambda c: c["score"],
            reverse=True,
        )
        candidates[req["id"]] = scored[:top_k]
    return candidates


# ── 판정 mock (유사도 임계값 기반) ─────────────────────────────────
_MET_THRESHOLD = 0.12
_WEAK_THRESHOLD = 0.04


def mock_judge(requirements: list[dict], candidates: dict) -> list[dict]:
    out: list[dict] = []
    for req in requirements:
        cand = candidates.get(req["id"], [])
        top = cand[0] if cand else None
        score = top["score"] if top else 0.0

        if score >= _MET_THRESHOLD:
            out.append({
                "id": req["id"],
                "status": "met",
                "evidence_ids": [top["sentence"]["id"]],
                "comment": "관련 문장과 의미가 충분히 일치합니다. (mock)",
                "suggestion": None,
            })
        elif score >= _WEAK_THRESHOLD:
            out.append({
                "id": req["id"],
                "status": "weak",
                "evidence_ids": [top["sentence"]["id"]],
                "comment": "관련 언급은 있으나 근거가 약합니다. (mock)",
                "suggestion": "구체적인 사례나 수치를 한 문장 보강하세요. (mock)",
            })
        else:
            out.append({
                "id": req["id"],
                "status": "missing",
                "evidence_ids": [],
                "comment": "자소서에서 관련 내용을 찾지 못했습니다. (mock)",
                "suggestion": "공고가 요구하는 항목입니다. 관련 경험이 있다면 추가하세요. (mock)",
            })
    return out
