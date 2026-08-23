"""Challenge content loading.

Challenge packs are authored as YAML in ``content/challenges/`` and are
authoritative data: every file is validated against ``schemas/challenge.schema.json``
at load time and chain links must resolve. Invalid packs fail loudly - never
silently skipped (PLAN.md section 7).
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from app.core.config import default_content_dir, default_schemas_dir

CHALLENGE_SCHEMA_FILE = "challenge.schema.json"


class ChallengeError(RuntimeError):
    """Raised when a challenge pack fails schema validation or chain checks."""


def _load_schema(schemas_dir: Path) -> dict[str, Any]:
    with (schemas_dir / CHALLENGE_SCHEMA_FILE).open("r", encoding="utf-8") as fh:
        doc: dict[str, Any] = json.load(fh)
    return doc


def scan_challenges(content_dir: Path, schemas_dir: Path) -> dict[str, dict[str, Any]]:
    """Scan ``content/challenges/*.yaml``, validate each, index by id."""
    validator = Draft202012Validator(_load_schema(schemas_dir))
    challenges: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for path in sorted((content_dir / "challenges").glob("*.yaml")):
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        if not isinstance(raw, dict):
            errors.append(f"  {path.name}: not a YAML mapping")
            continue
        file_errors = [
            f"  {path.name}: {err.message} (path: {list(err.absolute_path)})"
            for err in validator.iter_errors(raw)
        ]
        if file_errors:
            errors.extend(file_errors)
            continue
        cid = raw["id"]
        if cid in challenges:
            errors.append(f"  duplicate challenge id '{cid}' ({path.name})")
            continue
        challenges[cid] = raw

    errors.extend(_chain_errors(challenges))
    if errors:
        raise ChallengeError(
            "Invalid challenge pack:\n" + "\n".join(errors) + f"\n({len(challenges)} valid entries)"
        )
    return challenges


def _chain_errors(challenges: dict[str, dict[str, Any]]) -> list[str]:
    """Chain membership must reference existing ids; next pointers must resolve."""
    errors: list[str] = []
    for cid, ch in challenges.items():
        chain = ch.get("chain")
        if not chain:
            continue
        family = chain.get("family_id")
        if family and not any(
            other.get("chain", {}).get("family_id") == family
            for oid, other in challenges.items()
            if oid != cid
        ):
            errors.append(f"  {cid}: chain family '{family}' has no other members")
        nxt = chain.get("next_challenge_id")
        if nxt is not None and nxt not in challenges:
            errors.append(f"  {cid}: next_challenge_id '{nxt}' does not exist")
    return errors


@lru_cache(maxsize=1)
def load_challenges() -> dict[str, dict[str, Any]]:
    """Load the seeded challenge pack from the resolved content directory."""
    return scan_challenges(default_content_dir(), default_schemas_dir())


def list_challenges() -> list[dict[str, Any]]:
    """Summaries sorted by (family, level, id); hints excluded to avoid spoilers."""
    out: list[dict[str, Any]] = []
    for cid in sorted(load_challenges()):
        ch = load_challenges()[cid]
        chain = ch.get("chain") or {}
        out.append(
            {
                "id": cid,
                "title": ch["title"],
                "difficulty": ch["difficulty"],
                "mode": ch.get("mode", "challenge"),
                "narrative": ch.get("narrative"),
                "has_starting_graph": bool(ch.get("starting_graph_ref")),
                "hint_count": len(ch.get("hints") or []),
                "requirement_count": len(ch.get("requirements") or []),
                "chain": {
                    "family_id": chain.get("family_id"),
                    "level": chain.get("level"),
                    "next_challenge_id": chain.get("next_challenge_id"),
                }
                if chain
                else None,
            }
        )
    return out


def get_challenge(cid: str) -> dict[str, Any] | None:
    """Full challenge document by id, or None."""
    found = load_challenges().get(cid)
    return dict(found) if found else None


def load_starting_graph(ref: str) -> dict[str, Any] | None:
    """Resolve a starting_graph_ref to a golden architecture document."""
    path = default_content_dir() / "golden_architectures" / f"{ref}.json"
    if not path.is_file():
        raise ChallengeError(f"challenge starting_graph_ref '{ref}' missing fixture {path.name}")
    with path.open("r", encoding="utf-8") as fh:
        doc: dict[str, Any] = json.load(fh)
    return doc


def solution_path(cid: str) -> Path:
    """Reference-solution fixture location for a challenge id (test support)."""
    return default_content_dir() / "golden_architectures" / f"{cid}_solution.json"
