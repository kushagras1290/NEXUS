from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEXUS_", env_file=".env", extra="ignore", case_sensitive=False
    )

    env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] | str = ["http://localhost:3000"]
    auth_mode: Literal["dev_headers", "oidc"] = "dev_headers"
    oidc_issuer: str = ""
    oidc_audience: str = "nexus-api"
    oidc_jwks_url: str = ""

    opensearch_url: AnyHttpUrl = AnyHttpUrl("http://localhost:9200")
    opensearch_username: str = "admin"
    opensearch_password: str = "admin"
    opensearch_verify_certs: bool = False
    opensearch_index: str = "nexus-knowledge-v1"

    qdrant_url: AnyHttpUrl = AnyHttpUrl("http://localhost:6333")
    qdrant_api_key: str = ""
    qdrant_collection: str = "nexus-knowledge-v1"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    vector_size: int = 384

    postgres_dsn: str = "postgresql+asyncpg://nexus:nexus@localhost:5432/nexus"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "nexus"
    minio_secret_key: str = Field(default="change-me-now", repr=False)
    minio_secure: bool = False

    search_limit_max: int = Field(default=50, ge=1, le=200)
    request_timeout_seconds: float = Field(default=5.0, gt=0.1, le=30)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def validate_production(self) -> None:
        if self.env != "production":
            return
        if self.auth_mode != "oidc":
            raise ValueError("Production requires NEXUS_AUTH_MODE=oidc")
        if not self.oidc_issuer or not self.oidc_jwks_url:
            raise ValueError("Production OIDC requires issuer and JWKS URL")
        if self.minio_secret_key == "change-me-now":
            raise ValueError("Production MinIO secret must be changed")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings
