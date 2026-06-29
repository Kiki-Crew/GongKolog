"""3단계 — BGE-M3 임베딩 + 후보 검색 (스펙 v2 3장).

v2: 매칭 텍스트가 요구사항 text → 카테고리 criteria.
모델은 main.py lifespan에서 1회 로딩 후 set_model()로 주입.
벡터DB 불필요 — 답변 문장 수십 개라 numpy 행렬곱 한 방.

settings.mock_embedding=true 면 BGE-M3 대신 문자 n-gram Jaccard 유사도 사용.
numpy는 지연 import.
"""
from app.config import settings
from app.core import mock

_model = None


def set_model(model) -> None:
    """서버 시작 시(lifespan) 로딩된 BGE-M3 모델 주입."""
    global _model
    _model = model


def get_model():
    if _model is None:
        raise RuntimeError("임베딩 모델이 아직 로딩되지 않았습니다 (lifespan 확인).")
    return _model


def embed(texts: list[str]):
    # 정규화 → 내적 = 코사인 유사도
    return get_model().encode(texts, normalize_embeddings=True)

def _build_retrieval_queries(category: dict) -> list[str]:
    """
    카테고리 하나를 여러 관점의 검색 질문으로 확장합니다.

    이유:
    - criteria 하나만 임베딩하면 비슷한 문장만 반복해서 뽑힙니다.
    - 경험 배경, 본인 행동, 방법, 결과, 배운 점/직무 연결을 나누어 찾으면
      특정 직무 키워드 규칙 없이도 전 분야 자소서에 비교적 안정적으로 대응할 수 있습니다.
    """
    category_name = category.get("category", "")
    criteria = category.get("criteria", "")
    job_signals = " ".join(category.get("job_signals", []))

    base = f"{category_name}. {criteria}. {job_signals}".strip()

    return [
        base,
        f"{base}와 관련된 경험의 배경, 문제 상황, 목표",
        f"{base}와 관련된 본인 행동, 수행 과정, 판단 과정",
        f"{base}와 관련된 사용 방법, 자료 활용, 분석 또는 실행 방식",
        f"{base}와 관련된 결과, 변화, 배운 점, 직무 적용 방향",
    ]


def _make_sentence_windows(sentences: list[dict], window_size: int = 2) -> list[dict]:
    """
    인접 문장을 묶어 임베딩 검색 단위로 만듭니다.

    이유:
    - 자소서는 한 문장만으로 의미가 완결되지 않는 경우가 많습니다.
    - 예를 들어 방법은 앞 문장, 결과는 뒷 문장에 있을 수 있으므로
      2문장 단위로 묶어 검색하면 흐름이 덜 끊깁니다.
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


def _has_too_much_overlap(ids: list[str], used_ids: set[str], limit: float = 0.5) -> bool:
    """
    이미 선택된 후보와 문장 id가 많이 겹치면 제외합니다.

    이유:
    - s2+s3, s3+s4처럼 거의 같은 근거가 반복 선택되는 것을 줄입니다.
    - 단순 유사도 top_k보다 다양한 근거를 확보하기 위한 처리입니다.
    """
    if not ids:
        return False

    overlap_ratio = len(set(ids) & used_ids) / len(ids)
    return overlap_ratio >= limit


def _select_diverse_windows(sim, windows: list[dict], top_k: int) -> list[dict]:
    """
    여러 검색 질문별로 후보 윈도우를 고르게 선택합니다.

    구성:
    1. 각 검색 질문마다 가장 적절한 후보를 우선 선택합니다.
    2. 이미 선택된 후보와 많이 겹치는 후보는 건너뜁니다.
    3. 부족하면 전체 점수 기준으로 다시 채웁니다.
    """
    import numpy as np

    selected = []
    used_ids: set[str] = set()
    selected_window_indexes: set[int] = set()

    query_count, window_count = sim.shape

    # 1) 검색 질문별로 하나씩 먼저 선택합니다.
    for q_idx in range(query_count):
        order = np.argsort(sim[q_idx])[::-1]

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
            })
            used_ids.update(ids)
            selected_window_indexes.add(w_idx)
            break

        if len(selected) >= top_k:
            return selected

    # 2) 아직 부족하면 전체 최고 점수 기준으로 보충합니다.
    max_scores = sim.max(axis=0)
    order = np.argsort(max_scores)[::-1]

    for w_idx in order:
        window = windows[w_idx]
        ids = window["ids"]

        if w_idx in selected_window_indexes:
            continue

        if _has_too_much_overlap(ids, used_ids):
            continue

        selected.append({
            "window": window,
            "score": float(max_scores[w_idx]),
        })
        used_ids.update(ids)
        selected_window_indexes.add(w_idx)

        if len(selected) >= top_k:
            break

    return selected

def find_candidates(categories: list[dict], sentences: list[dict], top_k: int = 5) -> dict:
    """
    각 카테고리에 대해 판정용 답변 근거를 찾습니다.

    기존 방식:
    - criteria 1개와 문장 1개를 비교해 top_k 문장을 선택했습니다.

    수정 방식:
    - 카테고리를 여러 검색 관점으로 확장합니다.
    - 답변 문장을 2문장 단위 윈도우로 묶습니다.
    - 검색 질문별로 겹치지 않는 후보를 선택합니다.
    """
    if settings.mock_embedding:
        return mock.mock_find_candidates(categories, sentences, top_k)

    if not sentences:
        return {c["id"]: [] for c in categories}

    windows = _make_sentence_windows(sentences, window_size=2)
    window_vecs = embed([w["text"] for w in windows])

    candidates: dict = {}

    for category in categories:
        queries = _build_retrieval_queries(category)
        query_vecs = embed(queries)

        # shape: (검색 질문 수, 윈도우 수)
        sim = query_vecs @ window_vecs.T

        selected = _select_diverse_windows(sim, windows, top_k)

        candidates[category["id"]] = [
            {
                # 기존 judge.py와 mock 구조를 크게 깨지 않기 위해 대표 문장은 유지합니다.
                "sentence": item["window"]["sentences"][0],

                # 실제 판정 입력에는 이 context_sentences를 사용합니다.
                "context_sentences": item["window"]["sentences"],

                # evidence_ids 검증이나 디버깅에 쓸 수 있습니다.
                "source_ids": item["window"]["ids"],

                "score": item["score"],
            }
            for item in selected
        ]

    return candidates