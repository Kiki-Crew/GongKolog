"""저장된 자소서 DB 접근 계층 (v2 — items jsonb)."""
from app.services import _documents
from app.services.supabase_client import get_supabase

TABLE = "cover_letters"


def list_cover_letters(user_id: str) -> list[dict]:
    return _documents.list_docs(TABLE, user_id)


def create_cover_letter(user_id: str, title: str, items: list[dict]) -> dict:
    # v2: content 단일 본문이 아니라 [{question, answer}, ...] 묶음
    res = (
        get_supabase()
        .table(TABLE)
        .insert({"user_id": user_id, "title": title, "items": items})
        .execute()
    )
    return res.data[0]


def update_cover_letter(user_id: str, doc_id: str, fields: dict) -> dict | None:
    return _documents.update_doc(TABLE, user_id, doc_id, fields)


def name_exists(user_id: str, title: str, exclude_id: str | None = None) -> bool:
    return _documents.name_exists(TABLE, user_id, title, exclude_id)


def delete_cover_letter(user_id: str, doc_id: str) -> bool:
    return _documents.delete_doc(TABLE, user_id, doc_id)
