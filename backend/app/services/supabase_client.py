"""Supabase 클라이언트 싱글톤 (service_role 키 — 백엔드 전용, 스펙 5.2 택1-B).

데이터는 전부 FastAPI 경유. RLS는 service_role로 우회되므로
user_id 체크는 각 service 함수에서 직접 수행한다.
"""
from supabase import Client, create_client

from app.config import settings

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)
