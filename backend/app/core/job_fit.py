"""문항 단위 공고-답변 정합 확인용

목적:
- 사용자가 다른 직무·다른 산업의 채용공고에 자소서를 잘못 넣은 경우를 감지하기 위함
- mismatch로 판정되면 pipeline에서 met 판정을 강등(cap)해, 잘못된 공고인데 met 결과가 나오지 않기 위함

설계 원칙:
- 전이 가능한 경험(예: 카페 아르바이트 협업 경험 → 사무직 협업 문항)은
  mismatch가 아니다. 판정 기본값은 aligned이며,
  답변이 지목하는 지원 대상/직무/산업이 공고와 '명확히' 충돌할 때만 mismatch.
- LLM 호출 실패 시에는 게이트를 적용하지 않는다(unknown).
  시스템 장애를 사용자 감점으로 전가하지 않기 위함.
- 모델은 공고 컨텍스트용 모델(groq_job_context_*)을 재사용한다.
  입력이 짧아(문항 + 답변 미리보기 + 컨텍스트 요약) 32B급이면 충분하다.
- Pydantic 응답 스키마에는 별도 필드를 추가하지 않는다.
  pipeline에서 기존 Category 필드의 status/comment/suggestion만 보정한다.
"""

import json
import logging

from app.config import settings
from app.core.llm import (
    LLMDailyTokenLimitError,
    LLMRequestTooLargeError,
    call_with_model_fallback_messages,
)
from app.core.prompts import JOB_FIT_SYSTEM_PROMPT, JOB_FIT_USER_TEMPLATE
from app.core.utils import safe_json

logger = logging.getLogger(__name__)

# 판정 결과 상수 — pipeline 게이팅과 프론트 표시에서 공유
ALIGNMENT_ALIGNED = "aligned"    # 공고와 정합. 게이트 미적용
ALIGNMENT_PARTIAL = "partial"    # 직무는 다르지만 전이 설명이 있음. 게이트 미적용(경고만)
ALIGNMENT_MISMATCH = "mismatch"  # 명백히 다른 직무/산업/기관 대상. met 강등
ALIGNMENT_UNKNOWN = "unknown"    # 판정 실패. 게이트 미적용

_VALID_ALIGNMENTS = {ALIGNMENT_ALIGNED, ALIGNMENT_PARTIAL, ALIGNMENT_MISMATCH}

# 게이트 판정에 넣을 직무 컨텍스트 최대 길이 — 비용/속도 보호
_JOB_CONTEXT_MAX_CHARS = 1600


def _fallback(alignment: str = ALIGNMENT_UNKNOWN, reason: str = "") -> dict:
    """게이트를 적용하지 않는 안전한 기본값."""
    return {
        "alignment": alignment,
        "reason": reason,
        "mismatch_signals": [],
    }


def _normalize_result(parsed) -> dict:
    """LLM 출력 스키마 보정 — 잘못된 값은 전부 unknown으로 무해화."""
    if not isinstance(parsed, dict):
        return _fallback()

    alignment = str(parsed.get("alignment") or "").strip().lower()
    if alignment not in _VALID_ALIGNMENTS:
        return _fallback()

    signals = [
        str(s).strip()
        for s in (parsed.get("mismatch_signals") or [])
        if isinstance(s, str) and str(s).strip()
    ][:3]

    # mismatch인데 답변에서 인용된 충돌 신호가 하나도 없으면 오탐 가능성이 높음
    # → partial로 완화 (게이트 미적용, 경고만 표시)
    if alignment == ALIGNMENT_MISMATCH and not signals:
        alignment = ALIGNMENT_PARTIAL

    return {
        "alignment": alignment,
        "reason": (parsed.get("reason") or "").strip(),
        "mismatch_signals": signals,
    }


def check_job_fit(
    job_context: str,
    question: str,
    answer_preview: str,
) -> dict:
    """문항 1개에 대해 공고-답변 정합성을 판정한다.

    Args:
        job_context: build_job_context() 산출물 (구조화된 직무 컨텍스트)
        question: 자소서 문항
        answer_preview: pipeline._build_answer_preview() 산출물 (핵심 문장 발췌)

    Returns:
        {"alignment": "aligned|partial|mismatch|unknown",
         "reason": str,
         "mismatch_signals": [str]}
    """

    if not answer_preview.strip():
        return _fallback()

    messages = [
        {"role": "system", "content": JOB_FIT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": JOB_FIT_USER_TEMPLATE.format(
                job_context=job_context[:_JOB_CONTEXT_MAX_CHARS],
                question=question,
                answer_preview=answer_preview,
            ),
        },
    ]

    try:
        raw = call_with_model_fallback_messages(
            messages,
            primary_model=settings.groq_job_context_primary_model,
            backup_model=settings.groq_job_context_backup_model,
            max_completion_tokens=400,
        )
        result = _normalize_result(safe_json(raw))
        logger.warning(
            "[JOB_FIT] alignment=%s signals=%s",
            result["alignment"],
            result["mismatch_signals"],
        )
        return result

    except (LLMDailyTokenLimitError, LLMRequestTooLargeError):
        # 토큰 한도류는 상위에서 429/413으로 변환해야 하므로 그대로 전파
        raise

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("[JOB_FIT JSON ERROR] error=%s", repr(e))
        return _fallback()

    except Exception as e:  # noqa: BLE001
        # 게이트 실패는 분석 자체를 막지 않는다
        logger.warning("[JOB_FIT LLM ERROR] error=%s", repr(e))
        return _fallback()