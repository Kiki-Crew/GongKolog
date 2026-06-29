"""Supabase JWT 검증 → user_id 추출 (FastAPI Depends, 스펙 6장).

토큰 서명 방식 두 가지를 모두 지원:
- HS256: 레거시 공유 시크릿(SUPABASE_JWT_SECRET)로 검증
- RS256/ES256: 새 키 체계 → Supabase JWKS(공개키)로 검증
"""
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


@lru_cache(maxsize=1)
def _jwks_client() -> "jwt.PyJWKClient":
    url = settings.supabase_url.strip().rstrip("/") + "/auth/v1/.well-known/jwks.json"
    return jwt.PyJWKClient(url)


def _decode(token: str) -> str:
    try:
        alg = jwt.get_unverified_header(token).get("alg", "HS256")
        if alg == "HS256":
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            signing_key = _jwks_client().get_signing_key_from_jwt(token).key
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[alg],
                audience="authenticated",
            )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"유효하지 않은 토큰: {e}")

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
