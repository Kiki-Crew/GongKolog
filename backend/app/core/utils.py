"""파싱 헬퍼 (스펙 4.4 5단계)."""
import json


def safe_json(text: str):
    """LLM 응답에서 코드펜스 제거 후 JSON 파싱."""
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(text)


def coerce_list(parsed) -> list:
    """LLM이 배열 대신 객체로 감싸 반환해도 내부 리스트를 꺼낸다.

    예) {"categories": [...]}, {"results": [...]} → [...]
    (Groq json_object 모드는 최상위가 객체여야 하므로 흔히 발생)
    리스트면 그대로, 못 찾으면 빈 리스트.
    """
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                return v
    return []
