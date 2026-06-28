"""Supabase 클라이언트 (service_role 키 — 백엔드 전용, 스펙 5.2 택1-B).

지연 생성: import 시점이 아니라 첫 호출 때 만든다.
→ Supabase 키/패키지 없이도 서버 부팅·분석(/api/analyze) 가능.
  (저장은 best-effort라 키 없으면 조용히 실패, 분석 결과는 반환)
"""
from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase():
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase 미설정 — .env의 SUPABASE_URL / SERVICE_ROLE_KEY 확인")
    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_role_key)
