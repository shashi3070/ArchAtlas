"""AI agent endpoints: explain, critique, hint, proposal.

Deterministic-first/AI-second: explain never fails (deterministic fallback),
everything else degrades loudly (503) when no provider is configured.
Proposals are strictly advisory - the backend never applies them.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents import service
from app.content import challenge_loader
from app.content.loader import load_catalog
from app.core.config import get_settings
from app.db import get_db
from app.evaluation import run_evaluation
from app.llm.gateway import (
    LLMRateLimited,
    LLMUnavailable,
    list_providers,
)
from app.llm.providers import LLMProviderError

router = APIRouter(prefix="/api/agent", tags=["agent"])

DbSession = Annotated[Session, Depends(get_db)]


def _502(exc: LLMProviderError) -> HTTPException:
    """Upstream provider failure - the caller should see the real reason."""
    return HTTPException(502, detail=f"LLM provider failed: {exc}")


class ExplainBody(BaseModel):
    result: dict[str, Any]


class GraphBody(BaseModel):
    graph: dict[str, Any]


class ProposalBody(GraphBody):
    goal: str = ""


class ChatBody(BaseModel):
    graph: dict[str, Any]
    messages: list[dict[str, Any]] = Field(default_factory=list)
    goal: str = ""
    provider_id: str = ""
    model: str = ""


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
    except LLMProviderError as exc:
        raise _502(exc) from exc


@router.get("/providers")
def providers() -> dict[str, Any]:
    """Availability matrix for the UI provider dropdown (no key values)."""
    return {"active": get_settings().llm_provider, "providers": list_providers()}


@router.get("/models")
def models(provider: str = "") -> dict[str, Any]:
    """Chat-capable model ids for a provider, fetched live from upstream.
    Degrades to {models: [], error} so the UI can fall back to the default."""
    from app.llm.gateway import defaults_model, list_provider_models

    if not provider.strip():
        raise HTTPException(422, detail="provider query parameter is required")
    default = defaults_model(provider.strip().lower(), get_settings())
    try:
        return {
            "provider": provider,
            "models": list_provider_models(provider),
            "default_model": default,
            "error": None,
        }
    except (LLMUnavailable, LLMProviderError) as exc:
        return {
            "provider": provider,
            "models": [],
            "default_model": default,
            "error": str(exc),
        }


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
    except LLMProviderError as exc:
        raise _502(exc) from exc


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
    except LLMProviderError as exc:
        raise _502(exc) from exc


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
    except LLMProviderError as exc:
        raise _502(exc) from exc


@router.post("/chat")
def chat(
    body: ChatBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> Any:
    """Full-context mentor chat. Fresh deterministic evaluation of the current
    canvas is attached every turn; the model must answer with strict JSON
    {reply, fix} where fix is a proposal-only graph edit."""
    if not body.messages:
        raise HTTPException(422, detail="messages must contain at least one entry")
    result = _evaluate(body.graph)
    try:
        return service.chat(
            db,
            x_client_key,
            result=result,
            graph=body.graph,
            messages=body.messages,
            goal=body.goal,
            provider_id=body.provider_id,
            model_override=body.model,
        )
    except service.AgentError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except LLMUnavailable as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except LLMRateLimited as exc:
        raise HTTPException(429, detail=str(exc), headers={"Retry-After": "3600"}) from exc
    except LLMProviderError as exc:
        raise _502(exc) from exc
