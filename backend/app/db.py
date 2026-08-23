"""Database engine and session management.

SQLite is the zero-friction local default; ``SDP_DATABASE_URL`` switches to
PostgreSQL (docker-compose) without code changes. Alembic migrations arrive
once the schema stabilizes - dev mode uses ``create_all`` at startup.
"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _database_url() -> str:
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite:///./"):
        # Make relative sqlite paths stable regardless of process cwd.
        name = url.removeprefix("sqlite:///./")
        return f"sqlite:///{Path(__file__).resolve().parents[2] / name}"
    return url


def create_db_engine() -> Engine:
    url = _database_url()
    kwargs: dict[str, object] = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_db_engine()
    return _ENGINE


def reset_engine_for_tests() -> None:
    """Point the process back at a fresh engine (used by test fixtures)."""
    global _ENGINE, _SESSION_FACTORY
    _ENGINE = None
    _SESSION_FACTORY = None


def get_session_factory() -> sessionmaker[Session]:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SESSION_FACTORY


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped session."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    from app.persistence import models  # noqa: F401  (register mappers)

    models.Base.metadata.create_all(get_engine())
