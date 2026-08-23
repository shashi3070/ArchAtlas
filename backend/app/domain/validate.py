"""Canonical-graph validation against the composite architecture schema.

Loads every ``schemas/*.schema.json`` into a ``referencing`` registry so the
composite ``architecture.schema.json`` can resolve its cross-file ``$ref`` s.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from app.core.config import default_schemas_dir


class GraphValidationError(ValueError):
    """Raised when an architecture document violates the canonical schema."""


@lru_cache(maxsize=1)
def _registry_and_validator(schemas_dir_str: str) -> tuple[Any, Draft202012Validator]:
    schemas_dir = Path(schemas_dir_str)
    resources: list[tuple[str, Resource]] = []
    for path in sorted(schemas_dir.glob("*.schema.json")):
        with path.open("r", encoding="utf-8") as fh:
            doc = json.load(fh)
        resource = Resource.from_contents(doc, default_specification=DRAFT202012)
        uri = f"{path.name}"
        resources.append((uri, resource))

    registry: Registry = Registry().with_resources(resources)
    with (schemas_dir / "architecture.schema.json").open("r", encoding="utf-8") as fh:
        composite = json.load(fh)
    return registry, Draft202012Validator(composite, registry=registry)


def get_graph_validator() -> Draft202012Validator:
    _, validator = _registry_and_validator(str(default_schemas_dir()))
    return validator


def validate_architecture_document(document: Any) -> None:
    """Raise GraphValidationError listing all violations, or return None."""
    errors = sorted(
        get_graph_validator().iter_errors(document),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        lines = []
        for err in errors[:20]:
            path = "/".join(str(p) for p in err.absolute_path) or "(root)"
            lines.append(f"  {path}: {err.message}")
        raise GraphValidationError("Invalid ArchitectureGraph:\n" + "\n".join(lines))


def normalize_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Fill semantic defaults the schema permits but callers may omit."""
    result = json.loads(json.dumps(graph))  # deep copy without mutation surprises
    for edge in result.get("edges", []):
        edge.setdefault("direction", "unidirectional")
        edge.setdefault("traffic_type", "sync_request")
        edge.setdefault("properties", {})
    for node in result.get("nodes", []):
        node.setdefault("properties", {})
        node.setdefault("capacity", {})
        node["availability"] = node.get("availability") or {}
    return result
