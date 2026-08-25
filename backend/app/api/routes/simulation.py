"""Simulation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.simulation.engine import simulate
from app.simulation.models import (
    SimulationInput,
    SimulationResult,
    SimulationRun,
    TrafficModel,
)

router = APIRouter(prefix="/api/simulate", tags=["simulation"])

# In-memory store (production would use DB)
_runs: dict[str, SimulationRun] = {}
_max_runs = 50


@router.post("", response_model=SimulationResult)
def run_simulation(inp: SimulationInput) -> SimulationResult:
    """Run analytical simulation over a graph + traffic model."""
    result = simulate(inp)

    # Persist the run
    run = SimulationRun(
        graph_hash=result.input_hash,
        traffic_rps=inp.traffic.total_rps,
        input_json=inp.model_dump(mode="json"),
        result_json=result.model_dump(mode="json"),
        result_summary=f"rps={inp.traffic.total_rps:.0f} "
        f"e2e_p95={result.summary.end_to_end.p95_ms:.0f}ms "
        f"cost=${result.summary.total_cost.total_usd_per_month:.2f}/mo",
    )
    _runs[run.id] = run

    # Evict old runs
    if len(_runs) > _max_runs:
        oldest = sorted(_runs.values(), key=lambda r: r.created_at)[: len(_runs) - _max_runs]
        for r in oldest:
            _runs.pop(r.id, None)

    return result


@router.get("/{run_id}")
def get_run(run_id: str) -> SimulationRun:
    """Retrieve a saved simulation run."""
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


@router.get("")
def list_runs() -> list[SimulationRun]:
    """List recent simulation runs."""
    return sorted(_runs.values(), key=lambda r: r.created_at, reverse=True)[:20]


@router.post("/quick")
def quick_simulate(graph_json: dict, total_rps: float = 1000) -> SimulationResult:
    """Quick simulation with defaults — useful for lab/canvas integration."""
    traffic = TrafficModel(total_rps=total_rps)
    inp = SimulationInput(graph_json=graph_json, traffic=traffic)
    return simulate(inp)
