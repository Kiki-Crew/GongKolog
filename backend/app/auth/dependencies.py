"""Supabase JWT 검증 → user_id 추출 (FastAPI Depends, 스펙 6장)."""
import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


def _decode(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰에 사용자 정보 없음")
    return user_id


def require_user(authorization: str | None = Header(default=None)) -> str:
    """로그인 필수 라우트용. user_id 반환."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "로그인이 필요합니다")
    return _decode(authorization.split(" ", 1)[1])


def optional_user(authorization: str | None = Header(default=None)) -> str | None:
    """비로그인 허용 라우트용 (분석 등). 토큰 있으면 user_id, 없으면 None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return _decode(authorization.split(" ", 1)[1])
    except HTTPException:
        return None
