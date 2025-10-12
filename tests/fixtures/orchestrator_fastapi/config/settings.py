"""
Configuration management using Pydantic Settings

This is a testable version of the Settings class from
roles/orchestrator_fastapi/templates/config/settings.py.j2

For testing, Jinja2 template variables are replaced with concrete defaults.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import List
from urllib.parse import quote


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields for testing flexibility
    )

    # Server configuration
    orchestrator_env: str = Field(default="production")
    orchestrator_host: str = Field(default="0.0.0.0")
    orchestrator_port: int = Field(default=8000)
    orchestrator_workers: int = Field(default=4)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Database (PostgreSQL)
    postgres_host: str = Field(default="hx-sqldb-server.dev-test.hana-x.ai")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="shield_orchestrator")
    postgres_user: str = Field(default="orchestrator")
    postgres_password: SecretStr = Field(default=SecretStr("default_password"))

    @property
    def database_url(self) -> str:
        # Use quote() with safe="" for proper URL userinfo encoding (asyncpg compatible)
        # quote_plus() encodes spaces as '+' which breaks asyncpg DSN parsing
        encoded_password = quote(self.postgres_password.get_secret_value(), safe="")
        return f"postgresql+asyncpg://{self.postgres_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Redis
    redis_host: str = Field(default="hx-sqldb-server.dev-test.hana-x.ai")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Qdrant
    qdrant_url: str = Field(
        default="https://hx-vectordb-server.dev-test.hana-x.ai:6333"
    )
    qdrant_api_key: SecretStr = Field(default=SecretStr("qdrant_key"))
    qdrant_collection: str = Field(default="hx_corpus_v1")
    qdrant_verify_ssl: bool = Field(default=False)

    # LLM (via LiteLLM)
    llm_api_base: str = Field(
        default="http://hx-litellm-server.dev-test.hana-x.ai:4000/v1"
    )
    llm_api_key: SecretStr = Field(default=SecretStr("llm_key"))
    llm_model: str = Field(default="llama3.2:latest")
    llm_embedding_model: str = Field(default="mxbai-embed-large")

    # CORS
    cors_origins: List[str] = Field(default=["*"])

    # Security
    jwt_secret_key: SecretStr = Field(default=SecretStr("jwt_secret"))
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)
