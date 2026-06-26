"""2단계 — 한국어 문장 분리 + id 부여 (스펙 4.4).

kss를 우선 사용하되, 미설치/실패 시 정규식 폴백으로 분리한다.
→ mock·테스트 환경에서 kss 없이도 동작.
"""
import re

# 문장 종결부( . ! ? 다/요/음 + 공백/끝 ) 기준 폴백 분리
_FALLBACK_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")


def _split_raw(text: str) -> list[str]:
    try:
        import kss

        return kss.split_sentences(text)
    except Exception:
        # kss 미설치 또는 분리 실패 → 정규식 폴백
        return _FALLBACK_SPLIT.split(text)


def split_sentences(cover_letter: str) -> list[dict]:
    raw = _split_raw(cover_letter)
    return [
        {"id": f"s{i + 1}", "text": s.strip()}
        for i, s in enumerate(raw)
        if s.strip()
    ]
