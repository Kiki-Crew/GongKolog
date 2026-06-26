"""공고 저장/조회/삭제 라우터 (스펙 6장, 인증 필요)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_user
from app.schemas.analysis import DocumentCreate
from app.services import job_postings as service

router = APIRouter(prefix="/api/job-postings", tags=["job-postings"])


@router.get("")
def list_docs(user_id: str = Depends(require_user)):
    return service.list_job_postings(user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doc(body: DocumentCreate, user_id: str = Depends(require_user)):
    return service.create_job_posting(user_id, body.title, body.content)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(doc_id: str, user_id: str = Depends(require_user)):
    if not service.delete_job_posting(user_id, doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
