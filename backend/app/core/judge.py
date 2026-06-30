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
    """
    LLM 판정 입력을 구성합니다.

    수정 이유:
    - 후보 문장 하나만 넘기면 앞뒤 맥락이 끊깁니다.
    - embedding.py에서 만든 context_sentences를 함께 넘겨
      경험 흐름을 조금 더 보존합니다.
    - job_signals는 공고 전체가 아니라 카테고리 판단에 필요한 보조 신호만 제공합니다.
    """
    blocks = []

    for category in categories:
        lines = [
            f'카테고리 {category["id"]}: {category["category"]}',
            f'기준: {category["criteria"]}',
        ]

        job_signals = category.get("job_signals", [])
        if job_signals:
            lines.append("채용공고 보조 신호:")
            for signal in job_signals[:3]:
                lines.append(f"- {signal}")

        cand = candidates.get(category["id"], [])

        if cand:
            lines.append("판정용 답변 근거:")

            for item in cand:
                role = item.get("role", "근거") # 추가
                context_sentences = item.get("context_sentences") or [item["sentence"]]

                context_text = " ".join(
                    f'{s["id"]}: {s["text"]}' for s in context_sentences
                )

                lines.append(f"- [{role}] {context_text}")
        else:
            lines.append("판정용 답변 근거: 없음")

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
