"""1단계 — 요구사항 추출 (스펙 4.4).

Groq 우선(구조적 추출·속도), 실패 시 Gemini 폴백.
JSON 파싱 실패 시 1회 재시도.
settings.mock_llm=true 면 규칙 기반 mock 사용 (키 불필요).
"""
import json

from app.config import settings
from app.core import mock
from app.core.llm import call_with_fallback
from app.core.prompts import EXTRACT_PROMPT
from app.core.utils import safe_json


def extract_requirements(job_posting: str) -> list[dict]:
    if settings.mock_llm:
        return mock.mock_extract(job_posting)

    prompt = EXTRACT_PROMPT.format(job_posting=job_posting)
    try:
        return safe_json(call_with_fallback(prompt, primary="groq", backup="gemini"))
    except (json.JSONDecodeError, ValueError):
        return safe_json(call_with_fallback(prompt, primary="groq", backup="gemini"))
