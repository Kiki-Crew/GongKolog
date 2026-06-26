"""2단계 — 한국어 문장 분리 + id 부여 (스펙 4.4)."""
import kss


def split_sentences(cover_letter: str) -> list[dict]:
    sentences = kss.split_sentences(cover_letter)
    return [
        {"id": f"s{i + 1}", "text": s.strip()}
        for i, s in enumerate(sentences)
        if s.strip()
    ]
