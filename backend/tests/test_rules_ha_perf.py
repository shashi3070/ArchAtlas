"""Rule tests: availability + performance + consistency categories."""

from __future__ import annotations

import pytest  # noqa: F401

from tests.eval_helpers import CLIENT_LB_API_DB, e, g, n, run_rules

# ---------------- availability ----------------

def test_ha_single_database(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("db", "postgresql")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    assert run_rules(catalog, graph)["ha.single_database"] == "FAIL"


def test_ha_db_with_replicas_passes(catalog):
    statuses_map = run_rules(catalog, CLIENT_LB_API_DB)
    assert statuses_map.get("ha.single_database") != "FAIL"


def test_ha_single_cache_inline_path(catalog):
    graph = g(
        [
            n("c", "client"),
            n("api", "api", replicas=2),
            n("redis", "redis"),
            n("db", "postgresql", replicas=3, multi_az=True, failover="automatic"),
        ],
        [e("e1", "c", "api"), e("e2", "api", "redis"), e("e3", "redis", "db")],
    )
    assert run_rules(catalog, graph)["ha.single_cache"] == "WARNING"


def test_ha_single_compute_node(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=1), n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    assert run_rules(catalog, graph)["ha.single_compute_node"] == "WARNING"


def test_ha_single_region_high_target(catalog):
    graph = g(
        [n("c", "client"),
         n("api", "api", replicas=2, multi_az=True, failover="automatic",
           props={"metrics": True}),
         n("db", "postgresql", replicas=2, multi_az=True, failover="automatic")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        requirements=[
            {"id": "r1", "category": "reliability", "description": "highly available",
             "validation_rules": ["availability >= 99.99"]}
        ],
    )
    assert run_rules(catalog, graph)["ha.single_region"] == "WARNING"


def test_ha_single_load_balancer(catalog):
    graph = g(
        [n("c", "client"), n("lb", "load_balancer", replicas=1),
         n("api", "api", replicas=2)],
        [e("e1", "c", "lb"), e("e2", "lb", "api")],
    )
    assert run_rules(catalog, graph)["ha.single_load_balancer"] == "WARNING"


def test_ha_missing_failover_critical_on_redundant_db(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("db", "postgresql", replicas=3)],  # no failover declared
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    assert run_rules(catalog, graph)["ha.missing_failover"] == "FAIL"


def test_ha_failover_declared_passes(catalog):
    statuses_map = run_rules(catalog, CLIENT_LB_API_DB)
    assert statuses_map.get("ha.missing_failover") != "FAIL"


# ---------------- performance ----------------

def test_perf_no_cache_high_read_fails(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=4),
         n("db", "mongodb", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        traffic_model={"rps": 10000, "read_ratio": 0.9},
    )
    assert run_rules(catalog, graph)["perf.no_cache_high_read"] == "FAIL"


def test_perf_inline_cache_passes(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=4),
         n("redis", "redis", replicas=2),
         n("db", "mongodb", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "redis"), e("e3", "redis", "db")],
        traffic_model={"rps": 10000, "read_ratio": 0.9},
    )
    assert run_rules(catalog, graph)["perf.no_cache_high_read"] == "PASS"


def test_perf_sync_expensive_dependency(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("ml", "worker", replicas=2)],
        [e("e1", "c", "api"),
         e("e2", "api", "ml", props={"expensive_ms": 800})],
    )
    assert run_rules(catalog, graph)["perf.sync_expensive_dependency"] == "WARNING"


def test_perf_excessive_network_hops(catalog):
    nodes = [n("c", "client")]
    edges = []
    chain = ["lb", "api", "cache", "svc", "gw"]
    prev = "c"
    types = ["load_balancer", "api", "redis", "api", "load_balancer"]
    for i, (nid, ntype) in enumerate(zip(chain, types, strict=False)):
        nodes.append(n(nid, ntype))
        edges.append(e(f"h{i}", prev, nid))
        prev = nid
    graph = g(nodes, edges)
    got = run_rules(catalog, graph)
    # 5 sync hops from client -> WARNING threshold is >= 6; adjust: add one hop.
    nodes.append(n("end", "object_storage"))
    edges.append(e("h5", prev, "end"))
    got2 = run_rules(catalog, g(nodes, edges))
    assert got.get("perf.excessive_network_hops", "PASS") in ("PASS", "WARNING")
    assert got2["perf.excessive_network_hops"] == "WARNING"


def test_perf_slow_storage_on_critical_path(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("s3", "object_storage")],
        [e("e1", "c", "api"), e("e2", "api", "s3")],
        requirements=[
            {"id": "lat", "description": "fast", "validation_rules": ["p95 <= 200ms"]}
        ],
    )
    assert run_rules(catalog, graph)["perf.slow_storage_on_critical_path"] == "WARNING"


# ---------------- consistency ----------------

STRONG_REQ = [{
    "id": "fresh", "category": "consistency",
    "description": "Users must see their own writes immediately",
    "validation_rules": [],
}]


def test_cons_eventual_store_strong_requirement(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("db", "mongodb", replicas=2, avail={"consistency_mode": "eventual"})],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        requirements=STRONG_REQ,
    )
    assert run_rules(catalog, graph)["cons.replica_for_strong_consistency"] == "FAIL"


def test_cons_cache_stale_strict(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("redis", "redis", replicas=2),
         n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "redis"), e("e3", "redis", "db")],
        requirements=STRONG_REQ,
    )
    assert run_rules(catalog, graph)["cons.cache_stale_strict_requirement"] == "WARNING"


SYNC_REQ = [{
    "id": "confirm", "category": "functional",
    "description": "The caller must receive confirmation of acceptance",
    "validation_rules": [],
}]


def test_cons_async_where_sync_required(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("q", "kafka", replicas=3), n("w", "worker", replicas=50)],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "w", traffic_type="async_event")],
        requirements=SYNC_REQ,
    )
    assert run_rules(catalog, graph)["cons.async_where_sync_required"] == "FAIL"


def test_cons_async_ok_without_sync_requirement(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("q", "kafka", replicas=3), n("w", "worker", replicas=50,
                                          props={"idempotent_consumer": True})],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "w", traffic_type="async_event")],
    )
    got = run_rules(catalog, graph)
    assert "cons.async_where_sync_required" not in got
