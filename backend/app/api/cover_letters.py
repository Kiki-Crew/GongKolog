"""자소서 저장/조회/삭제 라우터 (스펙 6장, 인증 필요)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_user
from app.schemas.analysis import DocumentCreate
from app.services import cover_letters as service

router = APIRouter(prefix="/api/cover-letters", tags=["cover-letters"])


@router.get("")
def list_docs(user_id: str = Depends(require_user)):
    return service.list_cover_letters(user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doc(body: DocumentCreate, user_id: str = Depends(require_user)):
    return service.create_cover_letter(user_id, body.title, body.content)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(doc_id: str, user_id: str = Depends(require_user)):
    if not service.delete_cover_letter(user_id, doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
