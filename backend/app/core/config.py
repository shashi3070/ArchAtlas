"""Application configuration. Env vars use the SDP_ prefix (e.g. SDP_CONTENT_DIR)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SDP_", env_file=".env", extra="ignore")

    app_name: str = "archatlas-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:8080",
    ]
    content_dir: Path | None = None
    database_url: str = "sqlite:///./sdp.db"

    # --- LLM gateway (Phase 5) ---
    # provider: none | openai | azure | groq | anthropic | gemini | ollama
    llm_provider: str = "none"
    llm_api_key: str = ""
    # Optional endpoint override. Required for azure (deployment root) and
    # ollama (e.g. http://localhost:11434); ignored otherwise unless set.
    llm_base_url: str = ""
    llm_model: str = ""
    # Per-client-key completed (non-cached) LLM calls per UTC day.
    llm_daily_limit: int = 200

    # Per-provider API keys (win over llm_api_key for that provider).
    openai_api_key: str = ""
    azure_api_key: str = ""
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # --- Auth (Google OAuth + JWT) ---
    google_client_id: str = ""
    google_client_secret: str = ""
    jwt_secret: str = "archatlas-dev-secret-change-in-production"

    # --- Rate limits ---
    free_daily_limit: int = 100
    free_cooldown_seconds: int = 10
    free_groq_daily_limit: int = 1000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def default_content_dir() -> Path:
    """Resolve the content directory: explicit setting, else repo-root detection."""
    settings = get_settings()
    if settings.content_dir is not None:
        return Path(settings.content_dir).resolve()
    # loader.py -> app/content/.. = app -> backend -> repo root
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "content"


def default_schemas_dir() -> Path:
    """Resolve the schemas directory alongside content."""
    return default_content_dir().parent / "schemas"
