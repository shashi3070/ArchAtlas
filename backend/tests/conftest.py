"""Shared pytest fixtures."""

import os
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.content.loader import load_catalog
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def isolated_db(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """Point the app at a throwaway sqlite file so test runs never touch sdp.db."""
    db_path = tmp_path_factory.mktemp("db") / "test.sqlite3"
    os.environ["SDP_DATABASE_URL"] = f"sqlite:///{db_path}"
    from app.core.config import get_settings
    from app.db import init_db, reset_engine_for_tests

    get_settings.cache_clear()
    reset_engine_for_tests()
    init_db()
    yield
    os.environ.pop("SDP_DATABASE_URL", None)
    get_settings.cache_clear()
    reset_engine_for_tests()


@pytest.fixture(scope="session")
def catalog() -> dict[str, dict[str, Any]]:
    return load_catalog()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client
