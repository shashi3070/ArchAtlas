"""Challenge scoring: deterministic requirement-driven grading.

A submission is scored by injecting the challenge's requirements (translated
into machine-checkable ``validation_rules``) into the submitted graph, running
the Phase-3 engine, and weighing the resulting outcomes:

    weights:  must=3  should=2  could=1
    factors:  satisfied=1.0  at_risk=0.5  violated=0.0  not_evaluable=0.0

    score_pct = sum(weight * factor) / sum(weight) * 100
    passed    = score_pct >= 70 AND no 'must' violated AND no hard
                constraint broken (allowed_components palette, max_nodes)

The engine stays the single source of truth - scoring never re-interprets
the graph, it only weighs the evidence the engine produced.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.content.loader import load_catalog
from app.domain.validate import (
    GraphValidationError,
    normalize_graph,
    validate_architecture_document,
)
from app.evaluation import canonical_json, run_evaluation

PASS_THRESHOLD = 70.0

_PRIORITY_WEIGHTS = {"must": 3, "should": 2, "could": 1}
_OUTCOME_FACTORS = {"satisfied": 1.0, "at_risk": 0.5, "violated": 0.0, "not_evaluable": 0.0}


class SubmissionError(ValueError):
    """Raised when a submission cannot be graded (invalid graph/constraints)."""


def validation_rules_for(req: dict[str, Any]) -> list[str]:
    """Translate a challenge requirement's metric/value/unit into expressions.

    The four machine-checkable families match requirements_map.py exactly;
    anything else stays qualitative (empty rules -> not_evaluable outcome).
    """
    metric = str(req.get("metric") or "")
    value = req.get("value")
    unit = str(req.get("unit") or "")
    if value is None:
        return []
    if metric == "rps":
        return [f"rps >= {value}"]
    if metric == "p95" and unit == "ms":
        return [f"p95 <= {value}ms"]
    if metric == "availability" and unit in ("%", "percent", "nines"):
        return [f"availability >= {value}"]
    if metric == "durability":
        return [f"durability >= {int(value)}"]
    return []


def build_requirement_docs(challenge: dict[str, Any]) -> list[dict[str, Any]]:
    """Challenge requirements -> graph requirement documents for the engine."""
    docs: list[dict[str, Any]] = []
    for req in challenge.get("requirements") or []:
        docs.append(
            {
                "id": req["id"],
                "category": req["category"],
                "description": req["description"],
                "priority": req.get("priority", "must"),
                "unit": req.get("unit"),
                "target": str(req.get("value")) if req.get("value") is not None else "",
                "validation_rules": validation_rules_for(req),
            }
        )
    return docs


def check_constraints(challenge: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    """Hard constraint violations; empty list means clean."""
    violations: list[str] = []
    allowed = challenge.get("allowed_components") or []
    node_types = {n.get("type", "unknown") for n in graph.get("nodes", [])}
    if allowed:
        off_palette = sorted(node_types - set(allowed) - {"client"})
        # clients are always drawable; every other component must be on-palette
        if "client" not in allowed and "client" in node_types:
            pass
        if off_palette:
            violations.append(f"components outside allowed palette: {', '.join(off_palette)}")
    max_nodes = _constraint_value(challenge, "max_nodes")
    if max_nodes is not None and len(graph.get("nodes", [])) > int(max_nodes):
        violations.append(f"node count {len(graph['nodes'])} exceeds max_nodes={max_nodes}")
    return violations


def _constraint_value(challenge: dict[str, Any], key: str) -> Any:
    for c in challenge.get("constraints") or []:
        if c.get("key") == key:
            return c.get("value")
    return None


def grade_submission(challenge: dict[str, Any], raw_graph: dict[str, Any]) -> dict[str, Any]:
    """Validate -> normalize -> evaluate -> score. Raises SubmissionError on
    schema-invalid graphs; hard-constraint breaches are reported in-band."""
    try:
        validate_architecture_document(raw_graph)
    except GraphValidationError as exc:
        raise SubmissionError(str(exc)) from exc

    graph = normalize_graph(raw_graph)
    graph["_raw_edges"] = [dict(e) for e in raw_graph.get("edges", [])]
    graph["requirements"] = build_requirement_docs(challenge)

    constraint_violations = check_constraints(challenge, graph)

    result = run_evaluation(
        graph,
        load_catalog(),
        architecture_id=None,
        architecture_version=int(graph.get("version", 1)),
    )

    breakdown: list[dict[str, Any]] = []
    earned = 0.0
    total = 0.0
    must_violated = False
    outcomes_by_id = {o["requirement_id"]: o for o in result.get("requirement_outcomes", [])}
    for doc in graph["requirements"]:
        priority = doc.get("priority", "must")
        weight = _PRIORITY_WEIGHTS.get(priority, 1)
        outcome = outcomes_by_id.get(doc["id"], {})
        status = outcome.get("status", "not_evaluable")
        factor = _OUTCOME_FACTORS.get(status, 0.0)
        points = round(weight * factor, 2)
        total += weight
        earned += points
        if priority == "must" and status == "violated":
            must_violated = True
        breakdown.append(
            {
                "requirement_id": doc["id"],
                "priority": priority,
                "status": status,
                "weight": weight,
                "points": points,
                "reason": outcome.get("reason"),
                "confidence": outcome.get("confidence"),
            }
        )

    score_pct = round(earned / total * 100, 1) if total else 100.0
    engine_overall = result.get("summary", {}).get("overall_status", "pass")
    has_blocking_failure = engine_overall == "fail"
    passed = (
        score_pct >= PASS_THRESHOLD
        and not must_violated
        and not constraint_violations
        and not has_blocking_failure
    )

    active_rules = challenge.get("evaluation_rules") or []
    findings = result.get("rule_results", [])
    if active_rules:
        findings = [f for f in findings if f["rule_id"] in set(active_rules)]

    return {
        "challenge_id": challenge["id"],
        "score": score_pct,
        "passed": passed,
        "breakdown": breakdown,
        "constraint_violations": constraint_violations,
        "blocking_failure": has_blocking_failure,
        "findings": findings,
        "spofs": result.get("spofs", []),
        "bottlenecks": result.get("bottlenecks", []),
        "recommendations": result.get("recommendations", []),
        "graph_hash": hashlib.sha256(canonical_json(graph).encode()).hexdigest(),
        "_engine_summary": result.get("summary", {}),
    }
