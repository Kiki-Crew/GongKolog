"""환경변수 설정(.env 로딩)"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM - Groq만 사용 (extract / judge 각각 다른 모델 사용)
    groq_api_key: str = ""

    # 단계별 모델 분리
    groq_extract_primary_model: str = "llama-3.3-70b-versatile"
    groq_extract_backup_model: str = "openai/gpt-oss-120b" # 백업

    groq_judge_primary_model: str = "openai/gpt-oss-120b"
    groq_judge_backup_model: str = "llama-3.3-70b-versatile" # 백업

    # 채용공고 원문을 문항별 분석용 직무 컨텍스트로 1회 구조화
    groq_job_context_primary_model: str = "qwen/qwen3-32b"
    groq_job_context_backup_model: str = "openai/gpt-oss-120b"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # Embedding
    embed_model: str = "BAAI/bge-m3"
    embed_device: str = "cpu"

    # Mock 모드
    #   MOCK_LLM=true       → LLM 호출 대신 규칙 기반 가짜 추출/판정
    #   MOCK_EMBEDDING=true → BGE-M3 대신 문자 n-gram Jaccard 유사도
    mock_llm: bool = False
    mock_embedding: bool = False

    # CORS
    frontend_origin: str = "http://localhost:5173"


settings = Settings()


