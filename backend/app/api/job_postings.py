"""공고 저장/조회/삭제 라우터 (스펙 6장, 인증 필요)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_user
from app.schemas.analysis import DocumentCreate, JobPostingUpdate
from app.services import job_postings as service

router = APIRouter(prefix="/api/job-postings", tags=["job-postings"])


@router.get("")
def list_docs(user_id: str = Depends(require_user)):
    return service.list_job_postings(user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doc(body: DocumentCreate, user_id: str = Depends(require_user)):
    if service.name_exists(user_id, body.title):
        raise HTTPException(status.HTTP_409_CONFLICT, "같은 이름의 공고가 이미 있습니다.")
    return service.create_job_posting(user_id, body.title, body.content)


@router.patch("/{doc_id}")
def update_doc(doc_id: str, body: JobPostingUpdate, user_id: str = Depends(require_user)):
    fields: dict = {}
    if body.title is not None:
        if service.name_exists(user_id, body.title, exclude_id=doc_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "같은 이름의 공고가 이미 있습니다.")
        fields["title"] = body.title
    if body.content is not None:
        fields["content"] = body.content
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "수정할 내용이 없습니다.")
    doc = service.update_job_posting(user_id, doc_id, fields)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(doc_id: str, user_id: str = Depends(require_user)):
    if not service.delete_job_posting(user_id, doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
