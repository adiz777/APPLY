import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

for directory in (DATA_DIR, UPLOADS_DIR, EXPORTS_DIR, SCREENSHOTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    apply_env: str = "development"
    apply_secret_key: str = "apply-local-dev-secret-key-change-in-production-32b"
    apply_encryption_key: str = ""
    database_url: str = f"sqlite:///{(DATA_DIR / 'apply.db').as_posix()}"
    apply_default_admin_email: str = "candidate@apply.local"
    apply_default_admin_password: str = "ChangeMeImmediately!2026"

    ai_default_provider: str = "deterministic"
    ai_fallback_enabled: bool = True

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-latest"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    playwright_headless: bool = True
    playwright_timeout_ms: int = 30000
    apply_require_human_approval: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
