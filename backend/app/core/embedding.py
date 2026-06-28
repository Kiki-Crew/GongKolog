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


def find_candidates(categories: list[dict], sentences: list[dict], top_k: int = 3) -> dict:
    """각 카테고리의 criteria와 답변 문장 간 유사도로 후보를 추린다."""
    if settings.mock_embedding:
        return mock.mock_find_candidates(categories, sentences, top_k)

    if not sentences:
        return {c["id"]: [] for c in categories}

    import numpy as np

    cat_vecs = embed([c["criteria"] for c in categories])  # criteria 기준
    sent_vecs = embed([s["text"] for s in sentences])
    sim = cat_vecs @ sent_vecs.T  # (카테고리수, 문장수)

    candidates: dict = {}
    for i, cat in enumerate(categories):
        scores = sim[i]
        top_idx = np.argsort(scores)[::-1][:top_k]
        candidates[cat["id"]] = [
            {"sentence": sentences[j], "score": float(scores[j])}
            for j in top_idx
        ]
    return candidates
