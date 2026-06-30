"""회원 탈퇴 (인증 필요).

Supabase Auth에서 사용자 삭제 → profiles ON DELETE CASCADE로
cover_letters / job_postings / analyses 까지 함께 정리된다.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_user
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/api/account", tags=["account"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user_id: str = Depends(require_user)):
    try:
        get_supabase().auth.admin.delete_user(user_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"회원 탈퇴 실패: {e}")
