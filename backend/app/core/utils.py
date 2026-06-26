"""파싱 헬퍼 (스펙 4.4 5단계)."""
import json


def safe_json(text: str):
    """LLM 응답에서 코드펜스 제거 후 JSON 파싱."""
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)
