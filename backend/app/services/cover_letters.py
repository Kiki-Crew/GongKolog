"""저장된 자소서 DB 접근 계층."""
from app.services import _documents

TABLE = "cover_letters"


def list_cover_letters(user_id: str) -> list[dict]:
    return _documents.list_docs(TABLE, user_id)


def create_cover_letter(user_id: str, title: str, content: str) -> dict:
    return _documents.create_doc(TABLE, user_id, title, content)


def delete_cover_letter(user_id: str, doc_id: str) -> bool:
    return _documents.delete_doc(TABLE, user_id, doc_id)
