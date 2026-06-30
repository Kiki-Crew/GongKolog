"""FastAPI 진입점.

- lifespan에서 BGE-M3 모델 1회 로딩 (스펙 4.1 / 4.5 — 요청마다 로딩 금지)
- CORS: 프론트 주소 허용
- 라우터 등록
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account, analyze, cover_letters, job_postings
from app.config import settings
from app.core import embedding


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 BGE-M3 1회 로딩 (~2GB, 첫 실행 시 다운로드)
    # mock_embedding 모드면 모델이 필요 없으니 건너뜀 (빠른 부팅 — 프론트 개발/HTTP 테스트용)
    if not settings.mock_embedding:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(settings.embed_model, device=settings.embed_device)
        embedding.set_model(model)
    yield
    # shutdown 정리 필요 시 여기에


app = FastAPI(title="GongKolog API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(cover_letters.router)
app.include_router(job_postings.router)
app.include_router(account.router)


@app.get("/health")
def health():
    return {"status": "ok"}
