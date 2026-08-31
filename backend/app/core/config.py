from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application configuration read only from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "local-hash-384"
    database_url: str = "sqlite:///./data/study_assistant.db"
    upload_dir: str = "./data/uploads"
    vector_dir: str = "./data/vectors"
    max_upload_mb: int = 20
    cors_origins: str = "http://localhost:5173"

    @field_validator("database_url", mode="before")
    @classmethod
    def default_blank_database_url(cls, value: str | None) -> str:
        """Treat an empty .env value as local development configuration."""
        return "sqlite:///./data/study_assistant.db" if not value else value

    def absolute_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def upload_path(self) -> Path:
        return self.absolute_path(self.upload_dir)

    @property
    def vector_path(self) -> Path:
        return self.absolute_path(self.vector_dir)

    @property
    def data_path(self) -> Path:
        return self.upload_path.parent

    @property
    def resolved_database_url(self) -> str:
        prefix = "sqlite:///./"
        if self.database_url.startswith(prefix):
            relative_path = self.database_url.removeprefix(prefix)
            return f"sqlite:///{PROJECT_ROOT / relative_path}"
        return self.database_url

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
