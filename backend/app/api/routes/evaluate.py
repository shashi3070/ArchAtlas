"""Evaluation API: POST /api/evaluate runs the deterministic engine inline.

Ephemeral evaluations need no save; passing an architecture_id records the
result against that document for history.
"""

import hashlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.content.loader import load_catalog
from app.db import get_db
from app.domain.validate import (
    GraphValidationError,
    normalize_graph,
    validate_architecture_document,
)
from app.evaluation import canonical_json, run_evaluation
from app.persistence.models import EvaluationRecord, SavedArchitecture

router = APIRouter(prefix="/api", tags=["evaluate"])

DbSession = Annotated[Session, Depends(get_db)]


class EvaluateBody(BaseModel):
    graph: dict[str, Any]
    architecture_id: str | None = None


@router.post("/evaluate")
def evaluate(
    body: EvaluateBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    try:
        validate_architecture_document(body.graph)
    except GraphValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    graph = normalize_graph(body.graph)
    catalog = load_catalog()
    graph_hash = hashlib.sha256(canonical_json(graph).encode()).hexdigest()
    # Preserve author intent for the traffic-type rule: normalization fills
    # sync_request defaults, so capture what the user actually drew.
    graph["_raw_edges"] = [dict(edge) for edge in body.graph.get("edges", [])]
    result = run_evaluation(
        graph,
        catalog,
        architecture_id=body.architecture_id,
        architecture_version=int(graph.get("version", 1)),
    )
    # Stamp time at the edge - the engine itself stays pure/deterministic.
    from app.persistence.models import utcnow

    result["evaluated_at"] = utcnow().isoformat() + "Z"

    arch_id = body.architecture_id
    if arch_id is not None and x_client_key:
        owned = (
            db.query(SavedArchitecture)
            .filter(
                SavedArchitecture.id == arch_id,
                SavedArchitecture.owner_key == x_client_key,
            )
            .first()
        )
        if owned is None:
            arch_id = None  # never attribute evaluations to foreign documents
    db.add(
        EvaluationRecord(
            owner_key=x_client_key,
            architecture_id=arch_id,
            graph_hash=graph_hash,
            result_json=canonical_json(result),
        )
    )
    return result
