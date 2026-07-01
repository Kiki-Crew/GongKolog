"""1단계 — 문항+공고 → 평가 카테고리 추출

Groq:
- 1차: settings.groq_extract_primary_model
- 백업: settings.groq_extract_backup_model
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
from app.core.prompts import EXTRACT_SYSTEM_PROMPT, EXTRACT_USER_TEMPLATE
from app.core.utils import coerce_list, safe_json

logger = logging.getLogger(__name__)


def extract_categories(
    question: str,
    job_posting: str,
    answer_preview: str = "",
) -> list[dict]:
    if settings.mock_llm:
        return mock.mock_extract_categories(question, job_posting)

    messages = [
        {
            "role": "system",
            "content": EXTRACT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": EXTRACT_USER_TEMPLATE.format(
                job_posting=job_posting,
                question=question,
                answer_preview=answer_preview.strip() or "제공되지 않음",
            ),
        },
    ]

    # JSON 파싱 실패나 빈 응답은 1회 더 시도
    # API 자체가 실패하면 call_with_model_fallback 내부에서 모델 백업을 먼저 수행
    for attempt in range(2):
        try:
            raw = call_with_model_fallback_messages(
                messages,
                primary_model=settings.groq_extract_primary_model,
                backup_model=settings.groq_extract_backup_model,
            )

            cats = coerce_list(
                safe_json(raw),
                preferred_key="categories",
            )

            if cats:
                return cats

            logger.warning("[EXTRACT EMPTY] attempt=%s raw=%s", attempt + 1, raw)

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("[EXTRACT JSON ERROR] attempt=%s error=%s", attempt + 1, repr(e))
            continue

        except (LLMDailyTokenLimitError, LLMRequestTooLargeError):
            raise

        except Exception as e:  # noqa: BLE001
            # 두 Groq 모델이 모두 실패한 경우
            # 여기서 500 말고 빈 리스트를 반환하면 pipeline 쪽에서 안전하게 처리하게 수정
            logger.warning("[EXTRACT LLM ERROR] error=%s", repr(e))
            return []

    return []
