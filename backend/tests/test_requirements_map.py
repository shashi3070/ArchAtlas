"""Requirement expression mapping: rps / p95 / availability / durability."""

from __future__ import annotations

import copy

import pytest

from app.content.loader import load_catalog
from app.domain.validate import normalize_graph
from app.evaluation.context import EvalContext
from app.evaluation.requirements_map import map_requirements
from tests.eval_helpers import CLIENT_LB_API_DB, e, g, n


def _outcomes(graph: dict) -> dict[str, dict]:
    ctx = EvalContext(normalize_graph(graph), load_catalog())
    return {o["requirement_id"]: o for o in map_requirements(ctx)}


def _req(rid: str, rules: list[str], description: str = "throughput") -> dict:
    return {"id": rid, "description": description, "validation_rules": rules}


# ---------------- rps ----------------

def _api_fleet(replicas: int) -> dict:
    return g(
        [n("c", "client"), n("api", "api", replicas=replicas)],
        [e("e1", "c", "api")],
        traffic_model={"rps": 10000},
    )


def test_rps_satisfied_with_headroom():
    outcomes = _outcomes(g(_api_fleet(60)["nodes"], _api_fleet(60)["edges"],
                           traffic_model={"rps": 10000},
                           requirements=[_req("t", ["rps >= 45000"])]))
    assert outcomes["t"]["status"] == "satisfied"


def test_rps_at_risk_without_headroom():
    graph = _api_fleet(60)
    graph["requirements"] = [_req("t", ["rps >= 52000"])]
    # 60000 capacity: >= 52000 but below the 62400 (1.2x) headroom bar.
    assert _outcomes(graph)["t"]["status"] == "at_risk"


def test_rps_violated_below_target():
    graph = _api_fleet(2)  # catalog default 1000 rps x 2
    graph["requirements"] = [_req("t", ["rps >= 100000"])]
    assert _outcomes(graph)["t"]["status"] == "violated"


def test_rps_not_evaluable_without_api():
    graph = g([n("c", "client")], [])
    graph["requirements"] = [_req("t", ["rps >= 1000"])]
    outcome = _outcomes(graph)["t"]
    assert outcome["status"] == "not_evaluable"
    assert outcome["confidence"] == "low"


# ---------------- p95 ----------------

def test_p95_satisfied_short_chain():
    graph = copy.deepcopy(CLIENT_LB_API_DB)
    graph["requirements"] = [_req("lat", ["p95 <= 500ms"], "snappy")]
    outcome = _outcomes(graph)["lat"]
    assert outcome["status"] == "satisfied"
    assert outcome.get("confidence") == "low"


def test_p95_violated_long_chain():
    nodes = [n("c", "client")]
    edges = []
    prev = "c"
    chain = [("s1", "load_balancer"), ("s2", "api"), ("s3", "redis"),
             ("s4", "api"), ("s5", "load_balancer"), ("s6", "object_storage")]
    for nid, ntype in chain:
        nodes.append(n(nid, ntype))
        edges.append(e(f"h{nid}", prev, nid))
        prev = nid
    graph = g(nodes, edges)
    graph["requirements"] = [_req("lat", ["p95 <= 50ms"], "fast")]
    # 6 serial hops x 50ms base = 300ms >> 50ms.
    assert _outcomes(graph)["lat"]["status"] == "violated"


def test_p95_coarse_model_with_no_clients_scores_zero_hops():
    graph = g([n("a", "api")], [])
    graph["requirements"] = [_req("lat", ["p95 <= 100ms"])]
    outcome = _outcomes(graph)["lat"]
    # No client -> hop model measures 0 hops; confidence stays low because
    # the estimate carries no real evidence.
    assert outcome["status"] in ("satisfied", "not_evaluable")
    assert outcome.get("confidence") in ("low", "high")


# ---------------- availability ----------------

def test_availability_satisfied_full_redundancy():
    graph = copy.deepcopy(CLIENT_LB_API_DB)
    graph["requirements"] = [_req("ha", ["availability >= 99.9"], "uptime")]
    outcome = _outcomes(graph)["ha"]
    assert outcome["status"] in ("satisfied", "at_risk")


def test_availability_violated_single_critical():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("db", "postgresql")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    graph["requirements"] = [_req("ha", ["availability >= 99.95"], "uptime")]
    assert _outcomes(graph)["ha"]["status"] == "violated"


def test_availability_at_risk_without_failover():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("db", "postgresql", replicas=3)],  # redundant but failover undeclared
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    graph["requirements"] = [_req("ha", ["availability >= 99.9"], "uptime")]
    assert _outcomes(graph)["ha"]["status"] == "at_risk"


# ---------------- durability ----------------

def test_durability_satisfied_with_object_storage():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("s3", "object_storage")],
        [e("e1", "c", "api"), e("e2", "api", "s3")],
    )
    graph["requirements"] = [_req("d", ["durability >= 11"], "never lose bytes")]
    assert _outcomes(graph)["d"]["status"] == "satisfied"


def test_durability_violated_without_storage():
    graph = g([n("c", "client"), n("api", "api", replicas=2)], [e("e1", "c", "api")])
    graph["requirements"] = [_req("d", ["durability >= 11"], "keep data")]
    assert _outcomes(graph)["d"]["status"] == "violated"


# ---------------- aggregation & fallbacks ----------------

def test_no_validation_rules_is_not_evaluable_high_confidence():
    graph = g([n("c", "client")], [], requirements=[{"id": "v", "description": "nice"}])
    outcome = _outcomes(graph)["v"]
    assert outcome["status"] == "not_evaluable"
    assert outcome["confidence"] == "high"


def test_unsupported_expression_not_evaluable():
    graph = g([n("c", "client")], [], requirements=[_req("x", ["cost <= 5 dollars"])])
    assert _outcomes(graph)["x"]["status"] == "not_evaluable"


def test_worst_expression_wins_within_requirement():
    graph = _api_fleet(2)  # tiny capacity
    graph["traffic_model"] = {"rps": 10000}
    graph["requirements"] = [_req("mix", ["rps >= 10", "rps >= 100000"])]
    assert _outcomes(graph)["mix"]["status"] == "violated"


@pytest.mark.parametrize(
    "expression",
    ["RPS >= 50000", "rps>=50000", "throughput rps >= 50,000"],
)
def test_rps_expression_format_tolerant(expression: str):
    graph = _api_fleet(60)
    graph["requirements"] = [_req("t", [expression])]
    assert _outcomes(graph)["t"]["status"] in ("satisfied", "at_risk")
