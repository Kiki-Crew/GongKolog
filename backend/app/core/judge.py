"""4단계 — 카테고리 충족 판정 + 입력 빌더 (스펙 v2 3장).

Gemini 우선(한국어 추론), 실패 시 Groq 폴백.
파싱 실패/빈 결과 시 1회 재시도. 객체로 감싸 와도 리스트 추출.
settings.mock_llm=true 면 유사도 임계값 기반 mock 판정 (키 불필요).
"""
import json

from app.config import settings
from app.core import mock
from app.core.llm import call_with_fallback
from app.core.prompts import JUDGE_PROMPT
from app.core.utils import coerce_list, safe_json


def build_judge_input(categories: list[dict], candidates: dict) -> str:
    blocks = []
    for c in categories:
        lines = [f'카테고리 {c["id"]}: {c["category"]} — 기준: {c["criteria"]}']
        cand = candidates[c["id"]]
        if cand:
            lines.append("후보 답변 문장:")
            for x in cand:
                s = x["sentence"]
                lines.append(f'  - {s["id"]}: {s["text"]}')
        else:
            lines.append("후보 답변 문장: 없음")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def judge(categories: list[dict], candidates: dict) -> list[dict]:
    if settings.mock_llm:
        return mock.mock_judge(categories, candidates)

    prompt = JUDGE_PROMPT.format(judge_input=build_judge_input(categories, candidates))
    for _ in range(2):
        try:
            res = coerce_list(safe_json(call_with_fallback(prompt, primary="gemini", backup="groq")))
            if res:
                return res
        except (json.JSONDecodeError, ValueError):
            continue
    return []  # 끝까지 실패 → 조립부가 missing 기본값으로 안전하게 채움
