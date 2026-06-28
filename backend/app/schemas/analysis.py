"""Pydantic 모델 — 요청/응답 계약 (스펙 v2 2장).

v2: requirements[] 평면 → items[].categories[] 중첩.
`from`은 파이썬 예약어 → from_ + alias="from".
"""
from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    met = "met"
    weak = "weak"
    missing = "missing"


# ── 요청 ────────────────────────────────────────────────────────────
class AnalyzeItem(BaseModel):
    question: str
    answer: str


class AnalyzeRequest(BaseModel):
    job_posting: str
    items: list[AnalyzeItem]
    # 저장된 자소서/공고를 불러와 분석한 경우 연결용 (nullable)
    cover_letter_id: str | None = None
    job_posting_id: str | None = None


# ── 응답 ────────────────────────────────────────────────────────────
class Sentence(BaseModel):
    id: str
    text: str


class Category(BaseModel):
    id: str
    category: str
    from_: list[str] = Field(default_factory=list, alias="from")
    criteria: str
    status: Status
    evidence_ids: list[str]
    comment: str
    suggestion: str | None = None

    model_config = {"populate_by_name": True}


class ItemSummary(BaseModel):
    total: int
    met: int
    weak: int
    missing: int


class ItemResult(BaseModel):
    item_id: str
    question: str
    answer_sentences: list[Sentence]
    summary: ItemSummary
    categories: list[Category]


class OverallSummary(BaseModel):
    total_items: int
    total_categories: int
    met: int
    weak: int
    missing: int
    coverage_score: float | None = None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    overall_summary: OverallSummary
    items: list[ItemResult]

    model_config = {"populate_by_name": True}


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
