"""3단계 — BGE-M3 임베딩 + 후보 검색

v2: 매칭 텍스트가 요구사항 text → 카테고리 criteria
모델은 main.py lifespan에서 1회 로딩 후 set_model()로 주입
벡터DB 불필요 — 답변 문장 수십 개라 numpy 행렬곱 한 방
settings.mock_embedding=true 면 BGE-M3 대신 문자 n-gram Jaccard 유사도 사용
numpy는 지연 import
"""
from app.config import settings
from app.core import mock

_model = None


def set_model(model) -> None:
    """서버 시작 시(lifespan) 로딩된 BGE-M3 모델"""
    global _model
    _model = model


def get_model():
    if _model is None:
        raise RuntimeError("임베딩 모델이 아직 로딩되지 않았습니다 (lifespan 확인)")
    return _model


def embed(texts: list[str]):
    # 정규화 → 내적 = 코사인 유사도
    return get_model().encode(texts, normalize_embeddings=True)

def _build_retrieval_queries(category: dict) -> list[dict]:
    """
    카테고리별 검색 관점 생성
    -> 특정 직무에 치우치지 않고 상황, 행동, 방법, 결과, 적용 흐름을 찾음
    """
    category_name = category.get("category", "")
    criteria = category.get("criteria", "")
    job_signals = " ".join(category.get("job_signals", []))

    base = f"{category_name}. {criteria}".strip()
    job_hint = f"채용공고 보조 신호: {job_signals}" if job_signals else ""

    return [
        {
            "role": "카테고리 핵심 근거",
            "text": f"{base}. {job_hint}".strip(),
        },
        {
            "role": "상황·문제의식·목표",
            "text": f"{base}와 관련된 배경, 문제 상황, 목표, 지원 계기, 관심을 갖게 된 이유, 대상 또는 이해관계자",
        },
        {
            "role": "본인 역할·실행 과정",
            "text": f"{base}와 관련된 본인 역할, 행동, 판단 기준, 수행 과정, 의사결정, 협업 방식",
        },
        {
            "role": "방법·결과·배운 점·적용",
            "text": f"{base}와 관련된 사용한 방법, 산출물, 결과, 변화, 배운 점, 입사 후 적용 방향, 기여 가능성. {job_hint}".strip(),
        },
    ]


def _make_sentence_windows(sentences: list[dict], window_size: int = 3) -> list[dict]:
    """
    인접 문장을 묶어 임베딩 검색 단위로 생성
    -> 자소서는 한 문장만으로 의미가 완결되지 않는 경우가 많음
    """
    windows = []

    for start in range(len(sentences)):
        end = min(len(sentences), start + window_size)
        chunk = sentences[start:end]

        windows.append({
            "ids": [s["id"] for s in chunk],
            "text": " ".join(s["text"] for s in chunk),
            "sentences": chunk,
        })

    return windows


def _has_too_much_overlap(ids: list[str], used_ids: set[str], limit: float = 0.75) -> bool:
    """
    후보 간 과도한 문장 중복 방지
    -> 2문장 윈도우에서는 한 문장 겹침까지 허용
    """
    if not ids:
        return False

    overlap_ratio = len(set(ids) & used_ids) / len(ids)
    return overlap_ratio >= limit

_EXPERIENCE_HINTS = (
    "했습니다",
    "수행",
    "진행",
    "담당",
    "참여",
    "활용",
    "제작",
    "개발",
    "기획",
    "운영",
    "분석",
    "조사",
    "정리",
    "개선",
    "해결",
    "도출",
    "결과",
    "성과",
    "경험",
)

_INSIGHT_HINTS = (
    "배웠",
    "깨달",
    "알게",
    "느꼈",
    "이를 통해",
    "이를 바탕",
    "중요",
    "필요",
    "인사이트",
)

_APPLICATION_HINTS = (
    "입사 후",
    "지원 직무",
    "직무",
    "업무",
    "적용",
    "활용",
    "기여",
    "도움",
    "수행",
    "담당",
    "하고 싶",
    "하겠습니다",
)

_FUTURE_ONLY_HINTS = (
    "될 것입니다",
    "할 것입니다",
    "하겠습니다",
    "하고 싶습니다",
    "기여하겠습니다",
)


def _category_focus(category: dict) -> str:
    """
    카테고리의 평가 초점 추정
    -> 특정 직무가 아니라 자소서 평가 관점 기준
    """
    text = f'{category.get("category", "")} {category.get("criteria", "")}'

    if any(word in text for word in ("지원 동기", "지원동기", "선택한 이유", "지원 계기")):
        return "motivation"

    if any(word in text for word in ("입사 후", "목표", "포부", "적용", "활용", "기여", "직무 적용")):
        return "application"

    if any(word in text for word in ("경험", "근거", "역량", "강점", "수행 과정", "본인 역할")):
        return "experience"

    if any(word in text for word in ("배운 점", "인사이트", "성장", "가치관")):
        return "insight"

    return "general"


def _count_hints(text: str, hints: tuple[str, ...]) -> int:
    """문장 역할 판단용 힌트 개수"""
    return sum(1 for hint in hints if hint in text)


def _role_bonus(window_text: str, query_role: str, focus: str) -> float:
    """
    의미 유사도에 더할 문장 역할 보정값
    -> 지원자가 실제로 한 일과 배운 점을 더 잘 잡기 위한 일반 규칙
    """
    bonus = 0.0

    experience_score = _count_hints(window_text, _EXPERIENCE_HINTS)
    insight_score = _count_hints(window_text, _INSIGHT_HINTS)
    application_score = _count_hints(window_text, _APPLICATION_HINTS)
    future_only_score = _count_hints(window_text, _FUTURE_ONLY_HINTS)

    if focus == "experience":
        bonus += min(experience_score, 3) * 0.035
        bonus += min(insight_score, 2) * 0.015
        bonus -= min(future_only_score, 2) * 0.04

    elif focus == "application":
        bonus += min(application_score, 3) * 0.03
        bonus += min(insight_score, 2) * 0.025
        bonus += min(experience_score, 2) * 0.01

    elif focus == "motivation":
        bonus += min(application_score, 2) * 0.015
        bonus += min(insight_score, 2) * 0.02

    elif focus == "insight":
        bonus += min(insight_score, 3) * 0.04
        bonus += min(experience_score, 2) * 0.015

    else:
        bonus += min(experience_score + insight_score + application_score, 3) * 0.015

    if "결과·배운 점" in query_role or "적용" in query_role:
        bonus += min(insight_score + application_score, 3) * 0.02

    if "본인 역할" in query_role or "실행 과정" in query_role:
        bonus += min(experience_score, 3) * 0.025

    return bonus

def _select_diverse_windows(sim, windows: list[dict], queries: list[dict], top_k: int) -> list[dict]:
    """
    여러 검색 질문별로 후보 윈도우를 고르게 선택
    -> 단순히 문장만 고르면 LLM이 근거의 역할을 다시 추론
    -> 어떤 관점에서 뽑힌 후보인지 role을 함께 넘기면 judge 단계에서 판단 좋아짐
    """
    import numpy as np

    selected = []
    used_ids: set[str] = set()
    selected_window_indexes: set[int] = set()

    query_count, window_count = sim.shape

    # 1) 검색 질문별로 하나씩 먼저 선택
    for q_idx in range(query_count):
        order = np.argsort(sim[q_idx])[::-1]
        query = queries[q_idx]

        for w_idx in order:
            window = windows[w_idx]
            ids = window["ids"]

            if w_idx in selected_window_indexes:
                continue

            if _has_too_much_overlap(ids, used_ids):
                continue

            selected.append({
                "window": window,
                "score": float(sim[q_idx][w_idx]),
                "role": query["role"],
                "query_text": query["text"],
            })
            used_ids.update(ids)
            selected_window_indexes.add(w_idx)
            break

        if len(selected) >= top_k:
            return selected

    # 2) 아직 부족하면 전체 최고 점수 기준으로 보충
    max_scores = sim.max(axis=0)
    order = np.argsort(max_scores)[::-1]

    for w_idx in order:
        window = windows[w_idx]
        ids = window["ids"]

        if w_idx in selected_window_indexes:
            continue

        if _has_too_much_overlap(ids, used_ids):
            continue

        best_q_idx = int(sim[:, w_idx].argmax())
        best_query = queries[best_q_idx]

        selected.append({
            "window": window,
            "score": float(max_scores[w_idx]),
            "role": best_query["role"],
            "query_text": best_query["text"],
        })
        used_ids.update(ids)
        selected_window_indexes.add(w_idx)

        if len(selected) >= top_k:
            break

    return selected

def _get_context_sentences(
    sentences: list[dict],
    center_idx: int,
    window: int = 1,
) -> list[dict]:
    """
    후보 문장의 앞뒤 문맥을 함께 리턴
    -> center_idx가 s3이면 s2, s3, s4를 함께 반환(자기소개서 문장은 앞뒤 흐름이 중요; judge 단계에 문맥 전달)
    """
    start = max(0, center_idx - window)
    end = min(len(sentences), center_idx + window + 1)
    return sentences[start:end]


def find_candidates(categories: list[dict], sentences: list[dict], top_k: int = 4) -> dict:
    """카테고리별 다중 검색 질문과 문장 윈도우로 판정 후보를 찾음"""
    if settings.mock_embedding:
        return mock.mock_find_candidates(categories, sentences, top_k)

    if not sentences:
        return {c["id"]: [] for c in categories}

    candidates: dict = {}
    windows = _make_sentence_windows(sentences, window_size=2)

    if not windows:
        return {c["id"]: [] for c in categories}

    window_vecs = embed([w["text"] for w in windows])

    for category in categories:
        queries = _build_retrieval_queries(category)
        query_vecs = embed([q["text"] for q in queries])

        # 정규화 임베딩이므로 내적 = 코사인 유사도
        sim = query_vecs @ window_vecs.T

        # 의미 유사도 + 답변 역할 점수
        focus = _category_focus(category)

        for q_idx, query in enumerate(queries):
            for w_idx, window in enumerate(windows):
                sim[q_idx][w_idx] += _role_bonus(
                    window_text=window["text"],
                    query_role=query["role"],
                    focus=focus,
                )

        selected = _select_diverse_windows(
            sim=sim,
            windows=windows,
            queries=queries,
            top_k=top_k,
        )

        candidates[category["id"]] = [
            {
                # 기존 judge.py 호환용 대표 문장
                "sentence": item["window"]["sentences"][0],

                # 실제 판정용 문맥
                "context_sentences": item["window"]["sentences"],

                # judge가 근거 역할을 구분하도록 전달
                "role": item["role"],

                # 디버깅용 점수
                "score": item["score"],
            }
            for item in selected
        ]

    return candidates
