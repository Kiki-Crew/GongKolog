"""환경변수 설정. .env 로딩 (스펙 5.3 / 6장)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    gemini_api_key: str = ""
    groq_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "qwen-2.5-32b"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Embedding
    embed_model: str = "BAAI/bge-m3"
    embed_device: str = "cpu"

    # CORS
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
