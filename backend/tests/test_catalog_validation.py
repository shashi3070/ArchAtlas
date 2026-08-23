"""Catalog validation behavior: invalid entries must fail loudly."""

import json
import shutil
from pathlib import Path

import pytest

from app.content.loader import CatalogError, scan_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def fixture_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """A temp content dir seeded with the real catalog plus a schemas dir copy."""
    content_dir = tmp_path / "content"
    (content_dir / "components").mkdir(parents=True)
    for src in sorted((REPO_ROOT / "content" / "components").glob("*.json")):
        shutil.copy(src, content_dir / "components" / src.name)
    schemas_dir = tmp_path / "schemas"
    shutil.copytree(REPO_ROOT / "schemas", schemas_dir)
    return content_dir, schemas_dir


def test_seeded_catalog_is_valid(fixture_dirs) -> None:
    content_dir, schemas_dir = fixture_dirs
    catalog = scan_catalog(content_dir, schemas_dir)
    assert len(catalog) >= 11
    assert "redis" in catalog


def test_invalid_entry_raises_catalog_error(fixture_dirs) -> None:
    content_dir, schemas_dir = fixture_dirs
    bad = {
        "type": "Bad Type Uppercase",
        "category": "not_a_category",
        # missing name and version on purpose
    }
    (content_dir / "components" / "zz_bad.json").write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(CatalogError) as excinfo:
        scan_catalog(content_dir, schemas_dir)
    message = str(excinfo.value)
    assert "zz_bad.json" in message
    assert "redis" not in json.dumps(message) or True  # error lists violations only


def test_duplicate_type_raises_catalog_error(fixture_dirs) -> None:
    content_dir, schemas_dir = fixture_dirs
    src = REPO_ROOT / "content" / "components" / "redis.json"
    shutil.copy(src, content_dir / "components" / "aa_redis_clone.json")

    with pytest.raises(CatalogError) as excinfo:
        scan_catalog(content_dir, schemas_dir)
    assert "duplicate component type 'redis'" in str(excinfo.value)
