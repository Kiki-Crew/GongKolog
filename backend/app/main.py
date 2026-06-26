"""FastAPI 진입점.

- lifespan에서 BGE-M3 모델 1회 로딩 (스펙 4.1 / 4.5 — 요청마다 로딩 금지)
- CORS: 프론트 주소 허용
- 라우터 등록
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analyses, analyze
from app.api.routes.documents import cover_letters_router, job_postings_router
from app.config import settings
from app.services import embedding


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 BGE-M3 1회 로딩 (~2GB, 첫 실행 시 다운로드)
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
app.include_router(analyses.router)
app.include_router(cover_letters_router)
app.include_router(job_postings_router)


@app.get("/health")
def health():
    return {"status": "ok"}
