"""AI agent endpoints: explain, critique, hint, proposal.

Deterministic-first/AI-second: explain never fails (deterministic fallback),
everything else degrades loudly (503) when no provider is configured.
Proposals are strictly advisory - the backend never applies them.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents import service
from app.content import challenge_loader
from app.content.loader import load_catalog
from app.db import get_db
from app.evaluation import run_evaluation
from app.llm.gateway import LLMRateLimited, LLMUnavailable

router = APIRouter(prefix="/api/agent", tags=["agent"])

DbSession = Annotated[Session, Depends(get_db)]


class ExplainBody(BaseModel):
    result: dict[str, Any]


class GraphBody(BaseModel):
    graph: dict[str, Any]


class ProposalBody(GraphBody):
    goal: str = ""


def _evaluate(graph: dict[str, Any]) -> dict[str, Any]:
    return run_evaluation(
        graph,
        load_catalog(),
        architecture_id=None,
        architecture_version=int(graph.get("version", 1)),
    )


@router.post("/explain")
def explain(
    body: ExplainBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> Any:
    try:
        return service.explain_result(db, x_client_key, body.result)
    except LLMRateLimited as exc:
        raise HTTPException(429, detail=str(exc), headers={"Retry-After": "3600"}) from exc


@router.post("/critique")
def critique(
    body: GraphBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> Any:
    result = _evaluate(body.graph)
    try:
        return service.critique_graph(db, x_client_key, result, body.graph)
    except LLMUnavailable as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except LLMRateLimited as exc:
        raise HTTPException(429, detail=str(exc), headers={"Retry-After": "3600"}) from exc


@router.post("/challenges/{cid}/hint")
def challenge_hint(
    cid: str,
    level: int = 1,
    db: DbSession = None,  # type: ignore[assignment]
    body: dict[str, Any] | None = None,
    x_client_key: str | None = Header(default=None),
) -> Any:
    """LLM nudge at ``level`` without spoiling levels > level."""
    challenge = challenge_loader.get_challenge(cid)
    if challenge is None:
        raise HTTPException(status_code=404, detail=f"challenge '{cid}' not found")
    if level < 1:
        raise HTTPException(status_code=422, detail="level must be >= 1")
    ladder = challenge.get("hints") or []
    revealed = ladder[: max(0, level - 1)]
    graph = (body or {}).get("graph")
    try:
        return service.challenge_hint(
            db, x_client_key, challenge, level, revealed, graph
        )
    except LLMUnavailable as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except LLMRateLimited as exc:
        raise HTTPException(429, detail=str(exc), headers={"Retry-After": "3600"}) from exc


@router.post("/proposal")
def proposal(
    body: ProposalBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> Any:
    result = _evaluate(body.graph)
    try:
        return service.propose_diff(db, x_client_key, result, body.graph, body.goal)
    except service.AgentError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except LLMUnavailable as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except LLMRateLimited as exc:
        raise HTTPException(429, detail=str(exc), headers={"Retry-After": "3600"}) from exc
