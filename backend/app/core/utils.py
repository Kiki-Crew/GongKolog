"""파싱 헬퍼"""
import json


def safe_json(text: str):
    """LLM 응답에서 코드펜스 제거 후 JSON 파싱"""
    text = text.strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    elif text.startswith("```"):
        text = text.removeprefix("```").strip()

    if text.endswith("```"):
        text = text.removesuffix("```").strip()

    return json.loads(text)


def coerce_list(parsed, preferred_key: str | None = None) -> list:
    """
    LLM이 반환한 JSON에서 리스트를 꺼냄 (배열 바로 온 경우도 유지/다른 키로 감싸져도 첫번째 리스트 꺼내게)
    {"categories": [...]} 또는 {"judgments": [...]} 같은 응답 처리
    """
    if isinstance(parsed, list):
        return parsed

    if not isinstance(parsed, dict):
        return []

    if preferred_key and isinstance(parsed.get(preferred_key), list):
        return parsed[preferred_key]

    for value in parsed.values():
        if isinstance(value, list):
            return value

    return []