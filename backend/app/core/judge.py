"""4단계 — 충족 판정 + 입력 빌더 (스펙 4.4).

Gemini 우선(한국어 추론), 실패 시 Groq 폴백.
settings.mock_llm=true 면 유사도 임계값 기반 mock 판정 (키 불필요).
"""
import json

from app.config import settings
from app.core import mock
from app.core.llm import call_with_fallback
from app.core.prompts import JUDGE_PROMPT
from app.core.utils import safe_json


def build_judge_input(requirements: list[dict], candidates: dict) -> str:
    blocks = []
    for req in requirements:
        cand = candidates[req["id"]]
        lines = [f'요구사항 {req["id"]}: {req["text"]}']
        if cand:
            lines.append("후보 문장:")
            for c in cand:
                s = c["sentence"]
                lines.append(f'  - {s["id"]}: {s["text"]}')
        else:
            lines.append("후보 문장: 없음")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def judge(requirements: list[dict], candidates: dict) -> list[dict]:
    if settings.mock_llm:
        return mock.mock_judge(requirements, candidates)

    prompt = JUDGE_PROMPT.format(judge_input=build_judge_input(requirements, candidates))
    try:
        return safe_json(call_with_fallback(prompt, primary="gemini", backup="groq"))
    except (json.JSONDecodeError, ValueError):
        return safe_json(call_with_fallback(prompt, primary="gemini", backup="groq"))
