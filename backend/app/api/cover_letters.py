"""자소서 저장/조회/삭제 라우터 (v2 — items, 인증 필요)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_user
from app.schemas.analysis import CoverLetterCreate, CoverLetterUpdate
from app.services import cover_letters as service

router = APIRouter(prefix="/api/cover-letters", tags=["cover-letters"])


@router.get("")
def list_docs(user_id: str = Depends(require_user)):
    return service.list_cover_letters(user_id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_doc(body: CoverLetterCreate, user_id: str = Depends(require_user)):
    if service.name_exists(user_id, body.title):
        raise HTTPException(status.HTTP_409_CONFLICT, "같은 이름의 자소서가 이미 있습니다.")
    items = [it.model_dump() for it in body.items]
    return service.create_cover_letter(user_id, body.title, items)


@router.patch("/{doc_id}")
def update_doc(doc_id: str, body: CoverLetterUpdate, user_id: str = Depends(require_user)):
    fields: dict = {}
    if body.title is not None:
        if service.name_exists(user_id, body.title, exclude_id=doc_id):
            raise HTTPException(status.HTTP_409_CONFLICT, "같은 이름의 자소서가 이미 있습니다.")
        fields["title"] = body.title
    if body.items is not None:
        fields["items"] = [it.model_dump() for it in body.items]
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "수정할 내용이 없습니다.")
    doc = service.update_cover_letter(user_id, doc_id, fields)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doc(doc_id: str, user_id: str = Depends(require_user)):
    if not service.delete_cover_letter(user_id, doc_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "문서를 찾을 수 없습니다.")
