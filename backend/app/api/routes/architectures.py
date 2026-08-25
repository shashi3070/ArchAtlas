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
from app.domain.validate import (
    GraphValidationError,
    normalize_graph,
    validate_architecture_document,
)
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


# ── Share links ──────────────────────────────────────────────────────────────

class ShareResponse(BaseModel):
    share_url: str
    share_token: str


@router.post("/{arch_id}/share", response_model=ShareResponse)
def share_architecture(
    arch_id: str,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> ShareResponse:
    """Generate or return an existing share token for public access."""
    import secrets
    owner = _require_client_key(x_client_key)
    arch = _get_owned(db, owner, arch_id)
    if not arch.share_token:
        arch.share_token = secrets.token_hex(16)
        db.flush()
    return ShareResponse(
        share_url=f"/shared/{arch.share_token}",
        share_token=arch.share_token,
    )


@router.get("/shared/{token}")
def get_shared_architecture(
    token: str,
    db: DbSession,
) -> dict[str, Any]:
    """Public access to a shared architecture (no auth required)."""
    arch = db.scalars(
        select(SavedArchitecture).where(SavedArchitecture.share_token == token)
    ).first()
    if arch is None:
        raise HTTPException(status_code=404, detail="Shared architecture not found or link expired")
    row = db.scalars(
        select(ArchitectureVersion).where(
            ArchitectureVersion.architecture_id == arch.id,
            ArchitectureVersion.version == arch.current_version,
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=500, detail="Missing current version row")
    return {
        "id": arch.id,
        "name": arch.name,
        "current_version": arch.current_version,
        "updated_at": arch.updated_at.isoformat() + "Z",
        "graph": _loads(row.graph_json),
    }


# ── Compare mode ─────────────────────────────────────────────────────────────

class CompareBody(BaseModel):
    arch_id_a: str
    version_a: int
    arch_id_b: str
    version_b: int


def _diff_graphs(ga: dict, gb: dict) -> dict[str, Any]:
    """Compute a structural diff between two graph versions."""
    na = {n["id"]: n for n in ga.get("nodes", [])}
    nb = {n["id"]: n for n in gb.get("nodes", [])}
    ea = {e["id"]: e for e in ga.get("edges", [])}
    eb = {e["id"]: e for e in gb.get("edges", [])}

    added_nodes = [nb[nid] for nid in nb if nid not in na]
    removed_nodes = [na[nid] for nid in na if nid not in nb]
    modified_nodes = []
    for nid in na:
        if nid in nb and na[nid] != nb[nid]:
            modified_nodes.append({"id": nid, "before": na[nid], "after": nb[nid]})

    added_edges = [eb[eid] for eid in eb if eid not in ea]
    removed_edges = [ea[eid] for eid in ea if eid not in eb]
    modified_edges = []
    for eid in ea:
        if eid in eb and ea[eid] != eb[eid]:
            modified_edges.append({"id": eid, "before": ea[eid], "after": eb[eid]})

    return {
        "nodes_added": len(added_nodes),
        "nodes_removed": len(removed_nodes),
        "nodes_modified": len(modified_nodes),
        "edges_added": len(added_edges),
        "edges_removed": len(removed_edges),
        "edges_modified": len(modified_edges),
        "details": {
            "added_nodes": added_nodes,
            "removed_nodes": removed_nodes,
            "modified_nodes": modified_nodes,
            "added_edges": added_edges,
            "removed_edges": removed_edges,
            "modified_edges": modified_edges,
        },
    }


@router.post("/compare")
def compare_versions(
    body: CompareBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    """Compare two architecture versions and return a structural diff."""
    owner = _require_client_key(x_client_key)

    def _fetch_graph(arch_id: str, version: int) -> dict:
        arch = _get_owned(db, owner, arch_id)
        row = db.scalars(
            select(ArchitectureVersion).where(
                ArchitectureVersion.architecture_id == arch.id,
                ArchitectureVersion.version == version,
            )
        ).first()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Version {version} not found for {arch_id}")
        return _loads(row.graph_json)

    ga = _fetch_graph(body.arch_id_a, body.version_a)
    gb = _fetch_graph(body.arch_id_b, body.version_b)

    return {
        "arch_a": body.arch_id_a,
        "version_a": body.version_a,
        "arch_b": body.arch_id_b,
        "version_b": body.version_b,
        "diff": _diff_graphs(ga, gb),
    }


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
