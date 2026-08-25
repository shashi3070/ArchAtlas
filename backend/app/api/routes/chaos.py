"""Chaos engineering API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chaos.events import apply_chaos_event, get_event, list_events, run_chaos
from app.chaos.models import ChaosEvent, ChaosEventType, ChaosRun, ChaosRunResult

router = APIRouter(prefix="/api/chaos", tags=["chaos"])

# In-memory store
_runs: dict[str, ChaosRun] = {}
_max_runs = 30


class ChaosRunBody(BaseModel):
    graph_json: dict
    event_id: str
    traffic_rps: float | None = None


@router.get("/events")
def get_events() -> list[ChaosEvent]:
    """List all available chaos events."""
    return list_events()


@router.get("/events/{event_id}")
def get_event_detail(event_id: str) -> ChaosEvent:
    """Get details of a specific chaos event."""
    try:
        return get_event(ChaosEventType(event_id))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=f"Unknown event: {event_id}") from exc


@router.post("/run", response_model=ChaosRunResult)
def run_chaos_event(body: ChaosRunBody) -> ChaosRunResult:
    """Run a chaos scenario: before-simulate → inject → after-simulate → delta."""
    try:
        event_type = ChaosEventType(body.event_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid event_id: {body.event_id}") from exc

    result = run_chaos(
        graph=body.graph_json,
        event_id=event_type,
        traffic_rps=body.traffic_rps,
    )

    # Persist
    run = ChaosRun(
        event_id=body.event_id,
        result_json=result.model_dump(mode="json"),
        result_summary=(
            f"{result.event_name}: "
            f"avail {result.delta_report.availability_before:.1f}% → "
            f"{result.delta_report.availability_after:.1f}%, "
            f"p95 {result.delta_report.latency_p95_before:.0f}ms → "
            f"{result.delta_report.latency_p95_after:.0f}ms"
        ),
    )
    _runs[run.id] = run
    if len(_runs) > _max_runs:
        oldest = sorted(_runs.values(), key=lambda r: r.created_at)[: len(_runs) - _max_runs]
        for r in oldest:
            _runs.pop(r.id, None)

    return result


class InjectBody(BaseModel):
    graph_json: dict
    event_id: str


@router.post("/inject")
def inject_event(body: InjectBody) -> dict:
    """Apply a chaos event to a graph and return the modified graph (no simulation)."""
    try:
        event_type = ChaosEventType(body.event_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid event_id: {body.event_id}") from exc

    event = get_event(event_type)
    return apply_chaos_event(body.graph_json, event)


@router.get("/runs")
def list_runs() -> list[ChaosRun]:
    """List recent chaos runs."""
    return sorted(_runs.values(), key=lambda r: r.created_at, reverse=True)[:20]


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> ChaosRun:
    """Get a saved chaos run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Chaos run not found")
    return run
