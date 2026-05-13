"""Application settings via pydantic-settings."""

from functools import lru_cache
from typing import Any, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenRouter / LLM
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model_generation: str = "google/gemma-2-9b-it:free"
    llm_model_validation: str = "google/gemma-2-9b-it:free"
    llm_model_query: str = "google/gemma-2-9b-it:free"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Postgres
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "medical_db"
    postgres_user: str = "medical_user"
    postgres_password: str = "medical_password"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "medical_evidence"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "medical-artifacts"
    minio_use_ssl: bool = False

    # Evidence / retrieval thresholds
    evidence_min_chunks: int = 2
    evidence_min_avg_score: float = 0.55
    confidence_min_response: float = 0.45

    # Checkpointing: memory | redis | postgres
    checkpoint_backend: str = "memory"

    # Logging / tracing
    log_level: str = "INFO"
    otel_exporter_otlp_endpoint: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def drop_blank_numeric_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("postgres_port", "qdrant_port", "redis_port"):
                if data.get(key) == "":
                    data.pop(key, None)
        return data

    @field_validator("log_level")
    @classmethod
    def log_level_upper(cls, v: str) -> str:
        return v.upper()

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

