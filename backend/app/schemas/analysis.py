"""Pydantic 모델 — 요청/응답 계약 (스펙 6장 / 3장)."""
from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    met = "met"
    weak = "weak"
    missing = "missing"


# ── 분석 ────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    job_posting: str
    cover_letter: str
    # 저장된 자소서/공고를 불러와 분석한 경우 연결용 (nullable)
    cover_letter_id: str | None = None
    job_posting_id: str | None = None


class Sentence(BaseModel):
    id: str
    text: str


class Requirement(BaseModel):
    id: str
    text: str
    status: Status
    evidence_ids: list[str]
    comment: str
    category: str | None = None
    suggestion: str | None = None


class Summary(BaseModel):
    total: int
    met: int
    weak: int
    missing: int
    coverage_score: float | None = None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    summary: Summary
    cover_letter_sentences: list[Sentence]
    requirements: list[Requirement]


# ── 자소서 / 공고 저장 (마이페이지) ────────────────────────────────
class DocumentCreate(BaseModel):
    title: str
    content: str


class Document(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    created_at: str
