"""4단계 — 카테고리 충족 판정 + 입력 빌더

Groq only:
- 1차: settings.groq_judge_primary_model
- 백업: settings.groq_judge_backup_model
"""

import json
import logging

from app.config import settings
from app.core import mock
from app.core.llm import (
    LLMDailyTokenLimitError,
    LLMRequestTooLargeError,
    call_with_model_fallback_messages,
)
from app.core.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_USER_TEMPLATE
from app.core.utils import coerce_list, safe_json

logger = logging.getLogger(__name__)


def build_judge_input(categories: list[dict], candidates: dict) -> str:
    """
    LLM 판정 입력 생성
    -> 후보 문장 하나만 넘기면 앞뒤 맥락이 끊김
    (embedding.py에서 만든 context_sentences를 함께 넘겨 흐름을 보존, job_signals는 공고 전체가 아니라 카테고리 판단에 필요한 보조 신호만 제공)
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
                role = item.get("role", "근거")
                context_sentences = item.get("context_sentences") or [item["sentence"]]

                context_text = " ".join(
                    f'{sentence["id"]}: {sentence["text"]}'
                    for sentence in context_sentences
                )

                lines.append(f"- 근거 관점: {role}")
                lines.append(f"  답변 근거: {context_text}")
        else:
            lines.append("판정용 답변 근거: 없음")

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def judge(categories: list[dict], candidates: dict) -> list[dict]:
    if settings.mock_llm:
        return mock.mock_judge(categories, candidates)

    if not categories:
        return []

    judge_input = build_judge_input(categories, candidates)
    logger.warning("[JUDGE INPUT]\n%s", judge_input)

    messages = [
        {
            "role": "system",
            "content": JUDGE_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": JUDGE_USER_TEMPLATE.format(
                judge_input=judge_input,
            ),
        },
    ]

    for attempt in range(2):
        try:
            raw = call_with_model_fallback_messages(
                messages,
                primary_model=settings.groq_judge_primary_model,
                backup_model=settings.groq_judge_backup_model,
            )

            result = coerce_list(
                safe_json(raw),
                preferred_key="judgments",
            )

            if result:
                return result

            logger.warning("[JUDGE EMPTY] attempt=%s raw=%s", attempt + 1, raw)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("[JUDGE JSON ERROR] attempt=%s error=%s", attempt + 1, repr(e))
            continue

        except (LLMDailyTokenLimitError, LLMRequestTooLargeError):
            raise

        except Exception as e:  # noqa: BLE001
            # 두 Groq 모델이 모두 실패한 경우
            # 빈 리스트를 반환하면 pipeline._normalize_category()에서 missing으로 보정
            logger.warning("[JUDGE LLM ERROR] error=%s", repr(e))
            return []

    return []
