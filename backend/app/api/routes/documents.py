"""자소서 / 공고 저장·조회·삭제 (스펙 6장).

cover_letters 와 job_postings 는 스키마가 동일하므로 라우터 팩토리로 공용 처리.
user_id 체크를 코드에서 직접 수행 (스펙 5.2 택1-B).
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_user
from app.db.supabase_client import supabase
from app.models.schemas import DocumentCreate


def make_router(table: str, prefix: str, tag: str) -> APIRouter:
    router = APIRouter(prefix=f"/api/{prefix}", tags=[tag])

    @router.get("")
    def list_docs(user_id: str = Depends(require_user)):
        res = (
            supabase.table(table)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data

    @router.post("", status_code=status.HTTP_201_CREATED)
    def create_doc(body: DocumentCreate, user_id: str = Depends(require_user)):
        res = (
            supabase.table(table)
            .insert({"user_id": user_id, "title": body.title, "content": body.content})
            .execute()
        )
        return res.data[0]

    @router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_doc(doc_id: str, user_id: str = Depends(require_user)):
        # 본인 소유 확인 후 삭제
        owned = (
            supabase.table(table).select("id").eq("id", doc_id).eq("user_id", user_id).execute()
        )
        if not owned.data:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
        supabase.table(table).delete().eq("id", doc_id).eq("user_id", user_id).execute()

    return router


cover_letters_router = make_router("cover_letters", "cover-letters", "cover-letters")
job_postings_router = make_router("job_postings", "job-postings", "job-postings")
