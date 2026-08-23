"""Evaluation engine: normalize -> validate topology -> run rules -> compose.

The output matches schemas/evaluation.schema.json (validated by tests).
Determinism contract: identical input produces byte-identical JSON.
"""

from __future__ import annotations

import json
from typing import Any

from app.evaluation import metrics as metrics_mod
from app.evaluation import recommendations, spof
from app.evaluation.context import EvalContext
from app.evaluation.requirements_map import map_requirements
from app.evaluation.rules import RULES

RULE_VERSION = "3.0.0"


def run_evaluation(
    graph: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
    *,
    architecture_id: str | None = None,
    architecture_version: int | None = None,
) -> dict[str, Any]:
    ctx = EvalContext(graph, catalog)

    rule_results: list[dict[str, Any]] = []
    for rule_id in sorted(RULES):
        rule_results.extend(RULES[rule_id](ctx))

    scores = metrics_mod.dimension_scores(rule_results)
    overall = metrics_mod.overall_status(rule_results)
    spofs = spof.detect_spofs(ctx)
    bottlenecks = spof.detect_bottlenecks(ctx)
    req_outcomes = map_requirements(ctx)
    recs = recommendations.build_recommendations(ctx, rule_results)

    read_value, read_why = ctx.read_rps()
    write_value, write_why = ctx.write_rps()

    evaluation: dict[str, Any] = {
        "architecture_id": architecture_id,
        "architecture_version": architecture_version or 1,
        "rule_version": RULE_VERSION,
        "component_catalog_version": "0.1.0",
        "challenge_version": (graph.get("metadata") or {}).get("challenge_version"),
        # evaluated_at intentionally omitted - the caller stamps time so the
        # engine stays pure and byte-deterministic.
        "summary": {"overall_status": overall, "dimension_scores": scores},
        "rule_results": rule_results,
        "bottlenecks": bottlenecks,
        "spofs": spofs,
        "requirement_outcomes": req_outcomes,
        "recommendations": recs,
        "metrics": {
            "demand_rps_estimated": demand_metric(ctx),
            "read_rps_estimated": round(read_value, 1) if read_value is not None else None,
            "write_rps_estimated": round(write_value, 1) if write_value is not None else None,
            "read_demand_basis": read_why,
            "cache_inline": ctx.cache_is_inline(),
            "node_count": len(ctx.nodes),
            "edge_count": len(ctx.edges),
        },
    }
    return evaluation


def demand_metric(ctx: EvalContext) -> float | None:
    value = ctx.demand_rps()
    return round(value, 1) if value is not None else None


def canonical_json(evaluation: dict[str, Any]) -> str:
    """Stable serialization used for hashing and determinism tests."""
    return json.dumps(evaluation, sort_keys=True, separators=(",", ":"))
