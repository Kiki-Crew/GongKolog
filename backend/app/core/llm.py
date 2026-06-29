"""멀티 LLM 호출 추상화 + 폴백 + 일시오류 재시도 (스펙 4.3).

역할 분담: 추출=Groq(속도), 판정=Gemini(한국어 추론).
- call_llm: 일시 오류(503/500/타임아웃/overloaded)에 짧은 백오프로 재시도
- call_with_fallback: 한 제공자가 끝내 실패하면 다른 모델로 전환

무거운 SDK는 지연 import + 클라이언트 lazy 생성.
"""
import time
from functools import lru_cache

from app.config import settings

# 재시도할 일시 오류 신호 (대소문자 무시). 429/RESOURCE_EXHAUSTED(쿼터)는 제외 — 재시도해도 의미 적음.
_TRANSIENT_HINTS = (
    "503", "500", "502", "504",
    "unavailable", "overloaded", "high demand",
    "timeout", "timed out", "temporarily", "connection",
)
_MAX_RETRIES = 2
_BACKOFF_SEC = 1.5


@lru_cache(maxsize=1)
def _gemini_client():
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


@lru_cache(maxsize=1)
def _groq_client():
    from openai import OpenAI

    return OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def _is_transient(e: Exception) -> bool:
    code = getattr(e, "status_code", None) or getattr(e, "code", None)
    if code in (500, 502, 503, 504):
        return True
    s = str(e).lower()
    return any(h in s for h in _TRANSIENT_HINTS)


def _call_once(prompt: str, provider: str) -> str:
    if provider == "gemini":
        resp = _gemini_client().models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return resp.text
    elif provider == "groq":
        # 주의: Groq json_object 모드는 프롬프트에 'JSON' 단어 필요
        resp = _groq_client().chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    raise ValueError(provider)


def call_llm(prompt: str, provider: str) -> str:
    """일시 오류면 짧게 재시도 후 결국 실패하면 예외 전파."""
    last: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return _call_once(prompt, provider)
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < _MAX_RETRIES and _is_transient(e):
                time.sleep(_BACKOFF_SEC * (attempt + 1))
                continue
            raise
    raise last  # 도달 불가, 타입 안정용


def call_with_fallback(prompt: str, primary: str, backup: str) -> str:
    try:
        return call_llm(prompt, primary)
    except Exception:
        return call_llm(prompt, backup)
