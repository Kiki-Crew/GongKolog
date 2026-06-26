"""멀티 LLM 호출 추상화 + 폴백 (스펙 4.3).

역할 분담: 추출=Groq(속도), 판정=Gemini(한국어 추론).
한 제공자 실패 시 다른 모델로 자동 재시도.
"""
from google import genai
from openai import OpenAI

from app.config import settings

gemini_client = genai.Client(api_key=settings.gemini_api_key)
groq_client = OpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)


def call_llm(prompt: str, provider: str) -> str:
    if provider == "gemini":
        resp = gemini_client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return resp.text
    elif provider == "groq":
        # 주의: Groq json_object 모드는 프롬프트에 'JSON' 단어 필요
        resp = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    raise ValueError(provider)


def call_with_fallback(prompt: str, primary: str, backup: str) -> str:
    try:
        return call_llm(prompt, primary)
    except Exception:
        return call_llm(prompt, backup)
