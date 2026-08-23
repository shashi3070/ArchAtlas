"""Dimension scoring: deterministic mapping from rule results to 0-100 scores.

Severity weights (per category): critical=25, high=15, medium=8, low=3.
Statuses contribute: FAIL subtracts weight, WARNING subtracts half.
Scores start at 100 and clamp at 0; categories with no applicable rules
score 100 with status 'info' (nothing observed != perfect - UI labels it).
"""

from __future__ import annotations

from typing import Any

SEVERITY_WEIGHT = {"critical": 25.0, "high": 15.0, "medium": 8.0, "low": 3.0}

# Rule-id prefixes (graph., scale., ha., perf., cons., rel., sec., obs.)
# map onto the eight user-visible dimensions.
CATEGORY_DIMENSION = {
    "graph": "functionality",
    "scale": "scalability",
    "ha": "availability",
    "perf": "latency",
    "cons": "consistency",
    "rel": "availability",
    "sec": "security",
    "obs": "observability",
}

DIMENSIONS = [
    "functionality",
    "scalability",
    "availability",
    "latency",
    "consistency",
    "security",
    "cost",
    "observability",
]


def dimension_scores(rule_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    penalties: dict[str, float] = {d: 0.0 for d in DIMENSIONS}
    worst_status: dict[str, str] = {}

    for rr in rule_results:
        if rr.get("status") in ("PASS", "INFO"):
            continue
        if rr.get("confidence") == "low":
            continue  # unknowns must not punish scores
        rule_id = rr.get("rule_id", "")
        category = rule_id.split(".")[0]
        dimension = CATEGORY_DIMENSION.get(category)
        if dimension is None:
            continue
        weight = SEVERITY_WEIGHT.get(rr.get("severity", "medium"), 8.0)
        factor = 1.0 if rr.get("status") == "FAIL" else 0.5
        if rr.get("confidence") == "medium":
            factor *= 0.75
        penalties[dimension] += weight * factor
        prev = worst_status.get(dimension)
        if _worse(rr["status"], prev):
            worst_status[dimension] = rr["status"]

    out = []
    for dim in DIMENSIONS:
        score = max(0.0, round(100.0 - penalties[dim], 1))
        status = worst_status.get(dim) or "info"
        out.append({"dimension": dim, "score": score, "status": status.lower()})
    return out


def overall_status(rule_results: list[dict[str, Any]]) -> str:
    if any(
        rr.get("status") == "FAIL" and rr.get("severity") == "critical"
        for rr in rule_results
    ):
        return "fail"
    if any(rr.get("status") == "FAIL" for rr in rule_results):
        return "fail"
    if any(rr.get("status") == "WARNING" for rr in rule_results):
        return "warning"
    return "pass"


def _worse(new: str, old: str | None) -> bool:
    order = {"info": 0, "pass": 0, "unknown": 0, "warning": 1, "fail": 2}
    return order[new.lower()] > order.get((old or "").lower(), 0)
