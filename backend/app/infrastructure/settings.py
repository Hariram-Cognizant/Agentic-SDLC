from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Agentic SDLC"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/agentic_sdlc.db"
    artifact_dir: Path = Path("./artifacts")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    generation_provider: str = "template"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("generation_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"template", "ollama"}:
            raise ValueError("generation_provider must be 'template' or 'ollama'")
        return normalized


@lru_cache
def get_settings() -> Settings:
    return Settings()
