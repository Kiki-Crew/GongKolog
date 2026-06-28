"""환경변수 설정. .env 로딩 (스펙 5.3 / 6장)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Groq 모델은 수시로 폐기됨 → https://console.groq.com/docs/models 에서 현재 ID 확인.
    groq_model: str = "qwen/qwen3-32b"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Embedding
    embed_model: str = "BAAI/bge-m3"
    embed_device: str = "cpu"

    # Mock 모드 (키/모델 없이 파이프라인 검증용 — 스펙 8장 Tier 1)
    #   MOCK_LLM=true       → LLM 호출 대신 규칙 기반 가짜 추출/판정
    #   MOCK_EMBEDDING=true → BGE-M3 대신 문자 n-gram Jaccard 유사도
    mock_llm: bool = False
    mock_embedding: bool = False

    # CORS
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
