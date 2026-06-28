"""자소서/공고 공통 CRUD (cover_letters·job_postings 스키마 동일).

services/cover_letters.py, services/job_postings.py가 테이블명만 바꿔 재사용.
user_id 체크를 코드에서 직접 수행 (스펙 5.2 택1-B).
"""
from app.services.supabase_client import get_supabase


def list_docs(table: str, user_id: str) -> list[dict]:
    res = (
        get_supabase().table(table)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


def create_doc(table: str, user_id: str, title: str, content: str) -> dict:
    res = (
        get_supabase().table(table)
        .insert({"user_id": user_id, "title": title, "content": content})
        .execute()
    )
    return res.data[0]


def delete_doc(table: str, user_id: str, doc_id: str) -> bool:
    """본인 소유면 삭제 후 True, 없으면 False."""
    owned = (
        get_supabase().table(table).select("id").eq("id", doc_id).eq("user_id", user_id).execute()
    )
    if not owned.data:
        return False
    get_supabase().table(table).delete().eq("id", doc_id).eq("user_id", user_id).execute()
    return True
