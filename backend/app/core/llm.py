"""멀티 LLM 호출 추상화 + 폴백 + 일시오류 재시도.

수정 방향:
- Gemini 제거 & Groq provider만 유지
- extract / judge에서 모델명을 직접 넘길 수 있도록 구성
- 같은 Groq 안에서 primary_model 실패 시 backup_model로 전환

"""
import logging
import re
import time
from functools import lru_cache

from app.config import settings

logger = logging.getLogger(__name__)


class LLMDailyTokenLimitError(RuntimeError):
    """Groq 일일 토큰 한도 소진으로 분석을 계속할 수 없는 경우."""


class LLMRequestTooLargeError(RuntimeError):
    """단일 LLM 요청이 모델의 분당/요청 한도를 초과한 경우."""


def _model_name(provider: str) -> str:
    """로그에서 실제 사용된 LLM 모델명을 확인"""
    if provider == "gemini":
        return settings.gemini_model
    if provider == "groq":
        return settings.groq_model
    return provider

# 재시도할 일시 오류 신호
# 429는 재시도해도 바로 해결되지 않는 경우가 많으므로 여기서는 재시도 대상에서 제외
# primary 모델이 429로 실패 -> backup 모델 시도는 가능
_TRANSIENT_HINTS = (
    "503",
    "500",
    "502",
    "504",
    "unavailable",
    "overloaded",
    "high demand",
    "timeout",
    "timed out",
    "temporarily",
    "connection",
)
_MAX_RETRIES = 2
_BACKOFF_SEC = 1.5
_RATE_LIMIT_MAX_WAIT_SEC = 75.0
_RATE_LIMIT_DEFAULT_WAIT_SEC = 10.0
_RATE_LIMIT_COOLDOWN_SEC = 300
_MODEL_COOLDOWN_UNTIL: dict[str, float] = {}
_RESET_TIME_RE = re.compile(
    r"^\s*(?:(?P<days>\d+(?:\.\d+)?)d)?(?:(?P<hours>\d+(?:\.\d+)?)h)?(?:(?P<minutes>\d+(?:\.\d+)?)m)?(?:(?P<seconds>\d+(?:\.\d+)?)s)?\s*$"
)
_TRY_AGAIN_RE = re.compile(r"try again in\s+(?P<duration>(?:\d+(?:\.\d+)?[dhms]\s*)+)", re.IGNORECASE)
_DAILY_LIMIT_USER_MESSAGE = "하루에 사용 가능한 토큰 개수를 모두 소진했습니다."


@lru_cache(maxsize=1)
def _groq_client():
    """Groq는 OpenAI 호환 SDK로 호출"""
    from openai import OpenAI

    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY가 설정되지 않았습니다.")

    return OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

def _is_transient(e: Exception) -> bool: #일시 장애인지 판단
    if _is_rate_limited(e) or _is_request_too_large(e):
        return False

    code = getattr(e, "status_code", None) or getattr(e, "code", None)

    if code in (500, 502, 503, 504):
        return True

    s = str(e).lower()
    return any(hint in s for hint in _TRANSIENT_HINTS)


def _is_rate_limited(e: Exception) -> bool:
    code = getattr(e, "status_code", None) or getattr(e, "code", None)
    if code == 429:
        return True

    s = str(e).lower()
    return "rate limit" in s or "rate_limit" in s or "ratelimit" in s


def _exception_status_code(e: Exception):
    return getattr(e, "status_code", None) or getattr(e, "code", None)


def _exception_headers(e: Exception):
    response = getattr(e, "response", None)
    return getattr(response, "headers", None) or {}


def _parse_wait_seconds(value) -> float | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return max(0.0, float(text))
    except ValueError:
        pass

    match = _RESET_TIME_RE.match(text)
    if not match:
        return None

    days = float(match.group("days") or 0)
    hours = float(match.group("hours") or 0)
    minutes = float(match.group("minutes") or 0)
    seconds = float(match.group("seconds") or 0)
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def _message_wait_seconds(e: Exception) -> float | None:
    match = _TRY_AGAIN_RE.search(str(e))
    if not match:
        return None

    return _parse_wait_seconds(match.group("duration").strip().rstrip(".,;"))


def _header_wait_seconds(e: Exception) -> float | None:
    headers = _exception_headers(e)
    if not headers:
        return None

    for name in (
        "retry-after",
        "x-ratelimit-reset-tokens",
        "x-ratelimit-reset-requests",
    ):
        try:
            value = headers.get(name)
        except AttributeError:
            value = None

        seconds = _parse_wait_seconds(value)
        if seconds is not None:
            return seconds

    return None


def _is_daily_rate_limit(e: Exception) -> bool:
    text = str(e).lower()
    return (
        "per day" in text
        or "tpd" in text
        or "rpd" in text
        or "requests per day" in text
        or "tokens per day" in text
    )


def _is_request_too_large(e: Exception) -> bool:
    text = str(e).lower()
    return _exception_status_code(e) == 413 or "request too large" in text


def _rate_limit_wait_seconds(e: Exception) -> float | None:
    """분당 한도처럼 기다리면 풀리는 rate limit이면 대기 시간을 반환."""
    if not _is_rate_limited(e):
        return None

    # 일일 한도나 요청 1건 자체가 너무 큰 경우는 기다려도 해결되지 않습니다.
    if _is_daily_rate_limit(e) or _is_request_too_large(e):
        return None

    seconds = _header_wait_seconds(e)
    if seconds is None:
        seconds = _RATE_LIMIT_DEFAULT_WAIT_SEC

    seconds += 0.5
    if seconds > _RATE_LIMIT_MAX_WAIT_SEC:
        return None

    return seconds


def _rate_limit_header_snapshot(e: Exception) -> dict[str, str]:
    headers = _exception_headers(e)
    if not headers:
        return {}

    keys = (
        "retry-after",
        "x-ratelimit-limit-requests",
        "x-ratelimit-limit-tokens",
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-reset-requests",
        "x-ratelimit-reset-tokens",
    )
    snapshot: dict[str, str] = {}
    for key in keys:
        try:
            value = headers.get(key)
        except AttributeError:
            value = None
        if value is not None:
            snapshot[key] = str(value)
    return snapshot


def _log_daily_limit_error(e: Exception) -> None:
    logger.warning(
        "[LLM 일일 한도 초과] wait_seconds=%s header_wait_seconds=%s rate_limit_headers=%s error=%r",
        _message_wait_seconds(e),
        _header_wait_seconds(e),
        _rate_limit_header_snapshot(e),
        e,
    )


def _format_daily_limit_message(e: Exception) -> str:
    _log_daily_limit_error(e)
    return _DAILY_LIMIT_USER_MESSAGE


def _raise_terminal_llm_error(e: Exception) -> None:
    if _is_daily_rate_limit(e):
        raise LLMDailyTokenLimitError(_format_daily_limit_message(e)) from e

    if _is_request_too_large(e):
        raise LLMRequestTooLargeError(
            "분석 요청이 현재 모델의 처리 한도를 초과했습니다. 문항 수나 답변 길이를 줄여 다시 시도해 주세요."
        ) from e


def _cooldown_model(model: str) -> None:
    _MODEL_COOLDOWN_UNTIL[model] = time.time() + _RATE_LIMIT_COOLDOWN_SEC
    logger.warning(
        "[LLM 쿨다운] model=%s seconds=%s",
        model,
        _RATE_LIMIT_COOLDOWN_SEC,
    )


def _is_model_in_cooldown(model: str) -> bool:
    until = _MODEL_COOLDOWN_UNTIL.get(model)
    if not until:
        return False

    if until <= time.time():
        _MODEL_COOLDOWN_UNTIL.pop(model, None)
        return False

    return True


def _extra_body_for_model(model: str) -> dict:
    """
    모델별 추가 옵션을 구성
    GPT-OSS 계열은 reasoning 출력이 섞일 수 있으니 응답 본문에 안 섞이게 함(json 파싱 구조 중요)
    """
    if model.startswith("openai/gpt-oss"):
        return {
            "include_reasoning": False,
            "reasoning_effort": "low",
        }

    return {}

def _usage_get(obj, key: str, default=None):
    """OpenAI SDK objects and plain dicts both appear in usage details."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _log_usage(resp, model: str) -> None:
    """LLM 사용량 로그."""
    usage = getattr(resp, "usage", None)
    if not usage:
        return

    logger.warning(
        "[LLM 사용량] model=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
        model,
        _usage_get(usage, "prompt_tokens"),
        _usage_get(usage, "completion_tokens"),
        _usage_get(usage, "total_tokens"),
    )

def _call_once_messages(
    messages: list[dict[str, str]],
    model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """Groq 모델 1회 호출"""
    request_kwargs = {
        "model": model,
        "messages": messages,
        # JSON mode 사용
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_completion_tokens": max_completion_tokens,
    }

    extra_body = _extra_body_for_model(model)
    if extra_body:
        request_kwargs["extra_body"] = extra_body

    resp = _groq_client().chat.completions.create(**request_kwargs)

    _log_usage(resp, model)

    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("LLM 응답 내용이 비어 있습니다.")

    return content


def _call_once(
    prompt: str,
    model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """문자열 프롬프트 호환 호출"""
    return _call_once_messages(
        [{"role": "user", "content": prompt}],
        model,
        max_completion_tokens=max_completion_tokens,
    )


def call_groq_messages(
    messages: list[dict[str, str]],
    model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """
    일시 오류는 같은 모델에서 짧게 재시도
    quota, 인증 오류, JSON 형식 오류 등은 호출부 또는 fallback 함수에서 처리
    """
    last: Exception | None = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = _call_once_messages(
                messages,
                model,
                max_completion_tokens=max_completion_tokens,
            )

            logger.warning(
                "[LLM 성공] provider=groq model=%s",
                model,
            )

            return result

        except Exception as e:  # noqa: BLE001
            last = e

            wait_seconds = _rate_limit_wait_seconds(e)
            if attempt < _MAX_RETRIES and wait_seconds is not None:
                logger.warning(
                    "[LLM 대기] provider=groq model=%s attempt=%s seconds=%.1f error=%s",
                    model,
                    attempt + 1,
                    wait_seconds,
                    repr(e),
                )
                time.sleep(wait_seconds)
                continue

            if _is_rate_limited(e) or _is_request_too_large(e):
                raise

            if attempt < _MAX_RETRIES and _is_transient(e):
                logger.warning(
                    "[LLM 재시도] provider=groq model=%s attempt=%s error=%s",
                    model,
                    attempt + 1,
                    repr(e),
                )
                time.sleep(_BACKOFF_SEC * (attempt + 1))
                continue

            raise

    if last is not None:
        raise last

    raise RuntimeError("LLM 호출이 종료되었지만 성공 결과나 예외 정보가 없습니다.")


def call_groq(
    prompt: str,
    model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """문자열 프롬프트 호환 호출"""
    return call_groq_messages(
        [{"role": "user", "content": prompt}],
        model,
        max_completion_tokens=max_completion_tokens,
    )


def call_with_model_fallback_messages(
    messages: list[dict[str, str]],
    primary_model: str,
    backup_model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """같은 Groq provider 안에서 모델 fallback 수행"""
    if _is_model_in_cooldown(primary_model):
        logger.warning(
            "[LLM 폴백] provider=groq primary_model=%s reason=rate_limit_cooldown backup_model=%s",
            primary_model,
            backup_model,
        )
        try:
            return call_groq_messages(
                messages,
                backup_model,
                max_completion_tokens=max_completion_tokens,
            )
        except Exception as e:  # noqa: BLE001
            _raise_terminal_llm_error(e)
            raise

    try:
        return call_groq_messages(
            messages,
            primary_model,
            max_completion_tokens=max_completion_tokens,
        )

    except Exception as e:  # noqa: BLE001
        _raise_terminal_llm_error(e)

        if _is_rate_limited(e):
            _cooldown_model(primary_model)

        logger.warning(
            "[LLM 폴백] provider=groq primary_model=%s error=%s backup_model=%s",
            primary_model,
            repr(e),
            backup_model,
        )

        try:
            return call_groq_messages(
                messages,
                backup_model,
                max_completion_tokens=max_completion_tokens,
            )
        except Exception as backup_error:  # noqa: BLE001
            _raise_terminal_llm_error(backup_error)
            raise


def call_with_model_fallback(
    prompt: str,
    primary_model: str,
    backup_model: str,
    max_completion_tokens: int = 1200,
) -> str:
    """문자열 프롬프트 호환 fallback"""
    return call_with_model_fallback_messages(
        [{"role": "user", "content": prompt}],
        primary_model,
        backup_model,
        max_completion_tokens=max_completion_tokens,
    )

