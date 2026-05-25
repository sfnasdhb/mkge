from typing import Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: Literal["development", "production", "test"] = "development"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 50
    rate_limit_upload_per_hour: int = 5
    rate_limit_query_per_hour: int = 30
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # PostgreSQL
    database_url: str

    # Neo4j
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI
    gemini_api_key: str = ""
    groq_api_key: str = ""
    embedding_model: str = "models/text-embedding-004"
    embedding_dims: int = 768

    # Pipeline models (swap to gemini-3-flash / llama-4 khi available)
    gemini_parsing_model: str = "gemini-2.5-flash"
    gemini_ner_model: str = "gemini-2.5-flash"
    groq_verifier_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    verification_threshold: float = 0.7  # PROJECT_CONTEXT §13

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


settings = Settings()
