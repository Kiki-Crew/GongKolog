"""3단계 — BGE-M3 임베딩 + 후보 검색 (스펙 4.4).

모델은 main.py lifespan에서 1회 로딩 후 set_model()로 주입.
벡터DB 불필요 — 문장 수십 개라 numpy 행렬곱 한 방.

settings.mock_embedding=true 면 BGE-M3 대신 문자 n-gram Jaccard 유사도 사용
(2GB 모델 다운로드 없이 파이프라인 검증 — 스펙 8장 Tier 1).
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
    import numpy as np  # noqa: F401  (정규화 옵션이 내적=코사인 보장)

    # 정규화 → 내적 = 코사인 유사도
    return get_model().encode(texts, normalize_embeddings=True)


def find_candidates(requirements: list[dict], sentences: list[dict], top_k: int = 3) -> dict:
    if settings.mock_embedding:
        return mock.mock_find_candidates(requirements, sentences, top_k)

    if not sentences:
        return {r["id"]: [] for r in requirements}

    import numpy as np

    req_vecs = embed([r["text"] for r in requirements])
    sent_vecs = embed([s["text"] for s in sentences])
    sim = req_vecs @ sent_vecs.T  # (요구사항수, 문장수)

    candidates: dict = {}
    for i, req in enumerate(requirements):
        scores = sim[i]
        top_idx = np.argsort(scores)[::-1][:top_k]
        candidates[req["id"]] = [
            {"sentence": sentences[j], "score": float(scores[j])}
            for j in top_idx
        ]
    return candidates
