"""Unit tests for SPOF detection, dimension scoring, and recommendations."""

from __future__ import annotations

import pytest

from app.content.loader import load_catalog
from app.domain.validate import normalize_graph
from app.evaluation.context import EvalContext
from app.evaluation.metrics import SEVERITY_WEIGHT, dimension_scores, overall_status
from app.evaluation.recommendations import build_recommendations
from app.evaluation.spof import detect_bottlenecks, detect_spofs
from tests.eval_helpers import CLIENT_LB_API_DB, e, g, n


def _ctx(graph: dict) -> EvalContext:
    return EvalContext(normalize_graph(graph), load_catalog())


# ---------------- SPOF ----------------

def test_no_spofs_when_everything_redundant():
    assert detect_spofs(_ctx(CLIENT_LB_API_DB)) == []


def test_sole_api_is_total_spof():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=1),
         n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    spofs = {s["node_id"]: s for s in detect_spofs(_ctx(graph))}
    # Removing the lone api disconnects clients from every datastore.
    assert spofs["api"]["blast_radius"] == "total"


def test_sole_load_balancer_fronting_everything_total():
    graph = g(
        [n("c", "client"), n("lb", "load_balancer", replicas=1),
         n("api", "api", replicas=2), n("db", "postgresql", replicas=2)],
        [e("e1", "c", "lb"), e("e2", "lb", "api"), e("e3", "api", "db")],
    )
    spofs = {s["node_id"]: s for s in detect_spofs(_ctx(graph))}
    # Removing the lone lb disconnects clients from the datastore too,
    # so the data-access branch classifies it as total.
    assert spofs["lb"]["blast_radius"] == "total"


def test_lone_redis_partial_services():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("redis", "redis"),
         n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "redis"),
         e("e3", "redis", "db"), e("e4", "api", "db")],
    )
    spofs = {s["node_id"]: s for s in detect_spofs(_ctx(graph))}
    # Datastores stay reachable without redis, so its loss is only partial.
    assert spofs["redis"]["blast_radius"] == "partial"


def test_client_never_a_spof():
    graph = g([n("c", "client")], [])
    assert detect_spofs(_ctx(graph)) == []


# ---------------- bottlenecks ----------------

def test_db_bottleneck_when_utilization_high():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("db", "mongodb", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        traffic_model={"rps": 20000, "read_ratio": 0.5},
    )
    # writes 10000/s vs mongodb 8000 safe -> >100% utilization.
    btl = {b["node_id"] for b in detect_bottlenecks(_ctx(graph))}
    assert "db" in btl


def test_no_bottleneck_with_inline_cache():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=40,
                              capacity={"rps_per_instance": 5000}),
         n("redis", "redis", replicas=2),
         n("db", "mongodb", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "redis"), e("e3", "redis", "db")],
        traffic_model={"rps": 20000, "read_ratio": 0.9},
    )
    # reads 18000 x 0.1 cache factor = 1800 vs 15000 cap -> quiet.
    btl = detect_bottlenecks(_ctx(graph))
    assert [b for b in btl if b["node_id"] == "db"] == []


def test_api_tier_bottleneck_near_capacity():
    graph = g(
        [n("c", "client"), n("lb", "load_balancer", replicas=2),
         n("api", "api", replicas=2)],
        [e("e1", "c", "lb"), e("e2", "lb", "api")],
        traffic_model={"rps": 1800},  # 90% of 2 x 1000
    )
    btl = detect_bottlenecks(_ctx(graph))
    assert any(b["node_id"] == "api" and b["unit"] == "rps" for b in btl)


# ---------------- metrics ----------------

def _rr(rule_id: str, status: str, severity: str, confidence: str = "high") -> dict:
    return {"rule_id": rule_id, "status": status, "message": "m",
            "severity": severity, "confidence": confidence}


@pytest.mark.parametrize(
    "results,expected",
    [
        ([], "pass"),
        ([_rr("obs.no_logs", "WARNING", "low")], "warning"),
        ([_rr("rel.missing_idempotency", "FAIL", "high")], "fail"),
        ([_rr("ha.single_database", "FAIL", "critical")], "fail"),
        ([_rr("obs.no_metrics", "UNKNOWN", "medium")], "pass"),
    ],
)
def test_overall_status_precedence(results: list, expected: str):
    assert overall_status(results) == expected


def test_warning_costs_half_of_fail():
    warn = dimension_scores([_rr("scale.db_write_bottleneck", "WARNING", "critical")])
    fail = dimension_scores([_rr("scale.db_write_bottleneck", "FAIL", "critical")])
    w_score = next(d["score"] for d in warn if d["dimension"] == "scalability")
    f_score = next(d["score"] for d in fail if d["dimension"] == "scalability")
    assert w_score == round(100 - SEVERITY_WEIGHT["critical"] / 2, 1)
    assert f_score == round(100 - SEVERITY_WEIGHT["critical"], 1)


def test_medium_confidence_dampens_penalty():
    high = dimension_scores([_rr("scale.db_write_bottleneck", "FAIL", "critical")])
    med = dimension_scores(
        [_rr("scale.db_write_bottleneck", "FAIL", "critical", confidence="medium")]
    )
    h = next(d["score"] for d in high if d["dimension"] == "scalability")
    m = next(d["score"] for d in med if d["dimension"] == "scalability")
    assert m > h  # dampened penalty scores higher


def test_pass_and_info_results_free():
    scores = dimension_scores([_rr("sec.missing_authentication", "PASS", "high")])
    security = next(d for d in scores if d["dimension"] == "security")
    assert security["score"] == 100.0


def test_category_maps_to_dimension():
    scores = dimension_scores([_rr("sec.unencrypted_sensitive_flow", "FAIL", "high")])
    security = next(d for d in scores if d["dimension"] == "security")
    assert security["status"] == "fail"


def test_edge_category_rules_do_not_crash_scoring():
    scores = dimension_scores([_rr("edge.queue_unconsumed", "FAIL", "high")])
    assert len(scores) == 8  # edge.* has no dimension mapping; ignored safely


# ---------------- recommendations ----------------

def test_recommendation_for_read_bottleneck_names_catalog_components():
    graph = g(
        [n("c", "client"), n("api", "api", replicas=4),
         n("db", "mongodb", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        traffic_model={"rps": 50000, "read_ratio": 0.95},
    )
    ctx = _ctx(graph)
    from app.evaluation.rules import RULES

    real_results = [r for rid in sorted(RULES) for r in RULES[rid](ctx)]
    recs = build_recommendations(ctx, real_results)
    problems = {rec["problem"] for rec in recs}
    assert "Read demand exceeds datastore safe capacity" in problems
    cache_recs = [r for r in recs if r["problem"] == "Read demand exceeds datastore safe capacity"]
    assert cache_recs and "Catalog suggests" in cache_recs[0]["recommendation"]


def test_recommendation_without_catalog_match_still_composed():
    ctx = _ctx(CLIENT_LB_API_DB)
    recs = build_recommendations(ctx, [_rr("graph.no_ingress", "FAIL", "critical")])
    assert len(recs) == 1
    assert recs[0]["confidence"] == "medium"
    assert recs[0]["expected_benefit"]


def test_recommendations_skip_pass_and_unknown_rules():
    ctx = _ctx(CLIENT_LB_API_DB)
    recs = build_recommendations(
        ctx,
        [_rr("scale.db_read_bottleneck", "PASS", "critical"),
         _rr("scale.single_compute_high_traffic", "UNKNOWN", "critical",
             confidence="low")],
    )
    assert recs == []


def test_problem_map_entries_are_well_formed():
    from app.evaluation.recommendations import PROBLEM_MAP

    for _rule_id, (problem, tags, benefit) in PROBLEM_MAP.items():
        assert problem and benefit
        assert isinstance(tags, list)
