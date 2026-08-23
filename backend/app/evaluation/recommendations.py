"""Recommendations: turn failing rules into actionable, tradeoff-aware advice.

Grounded in the component catalog: suggested components come from entries
whose ``helps_with`` matches problem tags carried by each rule. No LLM.
"""

from __future__ import annotations

from typing import Any

from app.evaluation.context import EvalContext

# rule_id -> (problem statement, tags to match against catalog helps_with,
#             expected benefit). Tags use the catalog's own vocabulary so
#             candidates actually resolve.
PROBLEM_MAP: dict[str, tuple[str, list[str], str]] = {
    "scale.single_compute_high_traffic": (
        "API tier cannot serve declared traffic",
        ["request_processing", "horizontal_scaling_utilization"],
        "Request handling capacity meets demand with headroom",
    ),
    "scale.missing_load_balancing": (
        "No traffic distribution across instances",
        ["horizontal_scaling_utilization", "instance_failure_masking"],
        "Even utilization and instance failure masking",
    ),
    "scale.db_read_bottleneck": (
        "Read demand exceeds datastore safe capacity",
        ["database_read_load", "read_latency"],
        "Most reads served without touching the primary store",
    ),
    "scale.db_write_bottleneck": (
        "Write demand exceeds datastore write capacity",
        ["traffic_burst_buffering", "write_scaleout_via_sharding"],
        "Writes absorbed asynchronously or spread across shards",
    ),
    "perf.no_cache_high_read": (
        "Read-heavy workload hits storage directly",
        ["database_read_load", "api_latency_reduction"],
        "Lower latency and reduced database load",
    ),
    "ha.single_database": (
        "Database is a single point of failure",
        ["durable_primary_storage", "instance_failure_masking"],
        "Data access survives node loss",
    ),
    "ha.single_load_balancer": (
        "Load balancer is redundant-less entry point",
        ["instance_failure_masking", "horizontal_scaling_utilization"],
        "Ingress survives instance failure",
    ),
    "rel.queue_without_dlq": (
        "Poison messages can block queue processing",
        ["retry_and_dead_letter_flows", "async_processing"],
        "Bad messages isolated; pipeline keeps flowing",
    ),
    "edge.queue_unconsumed": (
        "Queue ingests events nobody consumes",
        ["task_distribution", "heavy_job_isolation"],
        "Events actually processed instead of piling up",
    ),
    "graph.no_ingress": (
        "No client entry point wired into the system",
        [],
        "Requests have somewhere to go",
    ),
}


def build_recommendations(
    ctx: EvalContext, rule_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rr in rule_results:
        if rr.get("status") not in ("FAIL", "WARNING"):
            continue
        mapping = PROBLEM_MAP.get(rr["rule_id"])
        if mapping is None:
            continue
        problem, tags, benefit = mapping
        candidates = _catalog_candidates(ctx, tags)
        rec: dict[str, Any] = {
            "problem": problem,
            "evidence": rr.get("evidence") or [rr.get("message", "")],
            "recommendation": _compose(rr, candidates),
            "expected_benefit": benefit,
            "tradeoffs": _tradeoffs(ctx, candidates),
            "confidence": "high" if candidates else "medium",
        }
        if candidates:
            rec["alternatives"] = [
                f"consider {entry['name']} ({entry['type']})" for entry in candidates[1:3]
            ]
        out.append(rec)
    return out[:8]


def _catalog_candidates(ctx: EvalContext, tags: list[str]) -> list[dict[str, Any]]:
    if not tags:
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in ctx.catalog.values():
        helps = set(entry.get("helps_with") or [])
        score = len(helps & set(tags))
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["type"]))
    return [entry for _, entry in scored]


def _compose(rr: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    actions = rr.get("suggested_actions") or []
    base = actions[0]["action"] if actions else "Address the finding"
    if candidates:
        names = ", ".join(c["name"] for c in candidates[:2])
        return f"{base}. Catalog suggests: {names}."
    return base


def _tradeoffs(ctx: EvalContext, candidates: list[dict[str, Any]]) -> list[str]:
    tradeoffs: list[str] = []
    for entry in candidates[:2]:
        tradeoffs.extend(str(t).replace("_", " ") for t in entry.get("tradeoffs") or [])
    return tradeoffs[:4]
