"""Supabase JWT 검증 → user_id 추출 (FastAPI Depends, 스펙 6장).

토큰 서명 방식 두 가지를 모두 지원:
- HS256: 레거시 공유 시크릿(SUPABASE_JWT_SECRET)로 검증
- RS256/ES256: 새 키 체계 → Supabase JWKS(공개키)로 검증

JWKS는 httpx로 가져온다(기본 certifi 인증서 사용 → macOS 등에서
PyJWKClient의 urllib SSL 인증서 오류 회피).
"""
from functools import lru_cache

import httpx
import jwt
from fastapi import Header, HTTPException, status

from app.config import settings


@lru_cache(maxsize=1)
def _jwks() -> "jwt.PyJWKSet":
    url = settings.supabase_url.strip().rstrip("/") + "/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return jwt.PyJWKSet.from_dict(resp.json())


def _signing_key(token: str):
    kid = jwt.get_unverified_header(token).get("kid")
    for k in _jwks().keys:
        if k.key_id == kid:
            return k.key
    # kid 못 찾으면 키 로테이션 가능성 → 캐시 비우고 1회 재조회
    _jwks.cache_clear()
    for k in _jwks().keys:
        if k.key_id == kid:
            return k.key
    raise jwt.PyJWTError(f"JWKS에서 kid={kid} 키를 찾지 못함")


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
            payload = jwt.decode(
                token,
                _signing_key(token),
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
