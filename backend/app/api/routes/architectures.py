"""Architectures API: CRUD with immutable, append-only versions.

Version rows are never mutated - "restore" appends a new version that copies
an old graph (PLAN.md section 15: version snapshots are immutable).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.domain.validate import GraphValidationError, normalize_graph, validate_architecture_document
from app.persistence.models import ArchitectureVersion, SavedArchitecture

router = APIRouter(prefix="/api/architectures", tags=["architectures"])

DbSession = Annotated[Session, Depends(get_db)]


def _require_client_key(x_client_key: str | None) -> str:
    if not x_client_key or len(x_client_key) < 8 or len(x_client_key) > 64:
        raise HTTPException(status_code=400, detail="Missing or invalid X-Client-Key header")
    return x_client_key


def _get_owned(db: Session, owner: str, arch_id: str) -> SavedArchitecture:
    arch = db.scalars(
        select(SavedArchitecture).where(
            SavedArchitecture.id == arch_id,
            SavedArchitecture.owner_key == owner,
        )
    ).first()
    if arch is None:
        raise HTTPException(status_code=404, detail="Architecture not found")
    return arch


class CreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    graph: dict[str, Any]
    challenge_id: str | None = Field(default=None, max_length=128)


class UpdateBody(BaseModel):
    graph: dict[str, Any]
    note: str = Field(default="", max_length=300)


class RestoreBody(BaseModel):
    version: int = Field(ge=1)


@router.post("")
def create_architecture(
    body: CreateBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    owner = _require_client_key(x_client_key)
    try:
        validate_architecture_document(body.graph)
    except GraphValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    graph = normalize_graph(body.graph)
    graph["version"] = 1
    if graph.get("id") in (None, ""):
        from app.persistence.models import new_uuid

        graph["id"] = new_uuid()[:8]

    arch = SavedArchitecture(owner_key=owner, name=body.name, current_version=1,
                             challenge_id=body.challenge_id)
    db.add(arch)
    db.flush()
    db.add(
        ArchitectureVersion(
            architecture_id=arch.id,
            version=1,
            graph_json=_dumps(graph),
        )
    )
    db.flush()
    return _meta(arch)


@router.get("")
def list_architectures(
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    owner = _require_client_key(x_client_key)
    rows = db.scalars(
        select(SavedArchitecture)
        .where(SavedArchitecture.owner_key == owner)
        .order_by(SavedArchitecture.updated_at.desc())
    ).all()
    return [_meta(a) for a in rows]


@router.get("/{arch_id}")
def get_architecture(
    arch_id: str,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    version_row = (
        db.scalars(
            select(ArchitectureVersion).where(
                ArchitectureVersion.architecture_id == arch.id,
                ArchitectureVersion.version == arch.current_version,
            )
        )
        .first()
    )
    if version_row is None:
        raise HTTPException(status_code=500, detail="Missing current version row")
    return {**_meta(arch), "graph": _loads(version_row.graph_json)}


@router.put("/{arch_id}")
def update_architecture(
    arch_id: str,
    body: UpdateBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    try:
        validate_architecture_document(body.graph)
    except GraphValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    graph = normalize_graph(body.graph)
    next_version = arch.current_version + 1
    graph["id"] = graph.get("id") or arch.id[:8]
    graph["version"] = next_version
    db.add(
        ArchitectureVersion(
            architecture_id=arch.id,
            version=next_version,
            graph_json=_dumps(graph),
            note=body.note,
        )
    )
    arch.current_version = next_version
    db.flush()
    return _meta(arch)


@router.get("/{arch_id}/versions")
def list_versions(
    arch_id: str,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    rows = db.scalars(
        select(ArchitectureVersion)
        .where(ArchitectureVersion.architecture_id == arch.id)
        .order_by(ArchitectureVersion.version)
    ).all()
    return [
        {
            "version": r.version,
            "note": r.note,
            "created_at": r.created_at.isoformat() + "Z",
            "is_current": r.version == arch.current_version,
        }
        for r in rows
    ]


@router.post("/{arch_id}/versions/{version}")
def get_version_graph(
    arch_id: str,
    version: int,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """Fetch any historical version's graph (read-only)."""
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    row = db.scalars(
        select(ArchitectureVersion).where(
            ArchitectureVersion.architecture_id == arch.id,
            ArchitectureVersion.version == version,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"version": row.version, "note": row.note, "graph": _loads(row.graph_json)}


@router.post("/{arch_id}/restore")
def restore_version(
    arch_id: str,
    body: RestoreBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """Restore by appending a NEW version with the old graph (immutability)."""
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    old = db.scalars(
        select(ArchitectureVersion).where(
            ArchitectureVersion.architecture_id == arch.id,
            ArchitectureVersion.version == body.version,
        )
    ).first()
    if old is None:
        raise HTTPException(status_code=404, detail="Version not found")

    graph = _loads(old.graph_json)
    next_version = arch.current_version + 1
    graph["version"] = next_version
    db.add(
        ArchitectureVersion(
            architecture_id=arch.id,
            version=next_version,
            graph_json=_dumps(graph),
            note=f"restored from v{body.version}",
        )
    )
    arch.current_version = next_version
    db.flush()
    return _meta(arch)


@router.delete("/{arch_id}")
def delete_architecture(
    arch_id: str,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, str]:
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    db.delete(arch)
    db.flush()
    return {"deleted": arch_id}


@router.get("/{arch_id}/export")
def export_architecture(
    arch_id: str,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> Response:
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    row = db.scalars(
        select(ArchitectureVersion).where(
            ArchitectureVersion.architecture_id == arch.id,
            ArchitectureVersion.version == arch.current_version,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=500, detail="Missing current version row")
    return Response(
        content=row.graph_json,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{arch.name}.architecture.json"'},
    )


def _dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _loads(raw: str) -> Any:
    import json

    return json.loads(raw)


def _meta(arch: SavedArchitecture) -> dict[str, Any]:
    return {
        "id": arch.id,
        "name": arch.name,
        "current_version": arch.current_version,
        "challenge_id": arch.challenge_id,
        "updated_at": arch.updated_at.isoformat() + "Z",
    }
