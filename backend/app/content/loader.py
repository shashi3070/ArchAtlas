"""Content loading and validation.

Content files are authoritative data validated against the canonical JSON
Schemas in ``schemas/`` at load time. Invalid catalog entries fail loudly -
never silently skip (PLAN.md section 7).
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from app.core.config import default_content_dir, default_schemas_dir

COMPONENT_SCHEMA_FILE = "component.schema.json"


class CatalogError(RuntimeError):
    """Raised when a component catalog entry fails schema validation."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def scan_catalog(content_dir: Path, schemas_dir: Path) -> dict[str, dict[str, Any]]:
    """Scan a content directory and validate every ``components/*.json`` entry.

    Returns a mapping of component type -> validated catalog entry.
    Raises CatalogError listing every violation if any entry is invalid.
    Separated from the cached wrapper so tests can point it at fixtures.
    """
    schema = _load_json(schemas_dir / COMPONENT_SCHEMA_FILE)
    validator = Draft202012Validator(schema)

    catalog: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    components_dir = content_dir / "components"
    for path in sorted(components_dir.glob("*.json")):
        entry = _load_json(path)
        file_errors = [
            f"  {path.name}: {err.message} (path: {list(err.absolute_path)})"
            for err in validator.iter_errors(entry)
        ]
        if file_errors:
            errors.extend(file_errors)
            continue
        ctype = entry["type"]
        if ctype in catalog:
            errors.append(f"  duplicate component type '{ctype}' ({path.name})")
            continue
        catalog[ctype] = entry

    if errors:
        raise CatalogError(
            "Invalid component catalog:\n" + "\n".join(errors) + f"\n({len(catalog)} valid entries)"
        )
    return catalog


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, dict[str, Any]]:
    """Load the seeded catalog from the resolved content directory."""
    return scan_catalog(default_content_dir(), default_schemas_dir())


def list_components() -> list[dict[str, Any]]:
    """All catalog entries sorted by type name."""
    return [load_catalog()[key] for key in sorted(load_catalog())]


def get_component(ctype: str) -> dict[str, Any] | None:
    """Fetch one catalog entry by type id, or None."""
    return load_catalog().get(ctype)


# ── Guide loader ──────────────────────────────────────────────────────

GUIDE_SCHEMA_FILE = "guide.schema.json"


def scan_guides(content_dir: Path) -> dict[str, dict[str, Any]]:
    """Scan content/guides/ and return {type: guide_data} for all valid JSON."""
    guides_dir = content_dir / "guides"
    if not guides_dir.is_dir():
        return {}
    guides: dict[str, dict[str, Any]] = {}
    for path in sorted(guides_dir.glob("*.json")):
        entry = _load_json(path)
        node_type = path.stem
        guides[node_type] = entry
    return guides


@lru_cache(maxsize=1)
def load_guides() -> dict[str, dict[str, Any]]:
    """Load all node guides from the content directory (cached)."""
    return scan_guides(default_content_dir())


def get_guide(ctype: str) -> dict[str, Any] | None:
    """Fetch one node guide by type id, or None."""
    return load_guides().get(ctype)
