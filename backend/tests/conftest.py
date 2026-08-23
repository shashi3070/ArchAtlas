"""Shared pytest fixtures."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.content.loader import load_catalog
from app.main import create_app


@pytest.fixture(scope="session")
def catalog() -> dict[str, dict[str, Any]]:
    return load_catalog()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client
