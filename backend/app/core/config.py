"""Application configuration. Env vars use the SDP_ prefix (e.g. SDP_CONTENT_DIR)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SDP_", env_file=".env", extra="ignore")

    app_name: str = "system-design-platform-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:8080",
    ]
    content_dir: Path | None = None


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
