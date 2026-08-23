"""Rule tests: reliability + security + observability + edge semantics."""

from __future__ import annotations

import pytest  # noqa: F401

from tests.eval_helpers import e, g, n, run_rules

BASE_NODES = [
    n("c", "client"),
    n("api", "api", replicas=2, props={"auth": True, "metrics": True}),
]


def test_rel_retries_without_timeout(catalog):
    graph = g(BASE_NODES + [n("svc", "api", replicas=2)],
              [e("e1", "c", "api"), e("e2", "api", "svc", props={"retry": True})])
    assert run_rules(catalog, graph)["rel.retries_without_timeout"] == "FAIL"


def test_rel_retry_with_timeout_and_backoff_clean(catalog):
    graph = g(BASE_NODES + [n("svc", "api", replicas=2)],
              [e("e1", "c", "api"),
               e("e2", "api", "svc",
                 props={"retry": True, "timeout_ms": 200, "backoff": "exponential"})])
    got = run_rules(catalog, graph)
    assert got.get("rel.retries_without_timeout") != "FAIL"
    assert got.get("rel.retries_without_backoff") != "WARNING"


def test_rel_retries_without_backoff(catalog):
    graph = g(BASE_NODES + [n("svc", "api", replicas=2)],
              [e("e1", "c", "api"),
               e("e2", "api", "svc", props={"retry": True, "timeout_ms": 100})])
    assert run_rules(catalog, graph)["rel.retries_without_backoff"] == "WARNING"


def test_rel_retry_amplification_needs_three_plus(catalog):
    nodes = list(BASE_NODES) + [n("s1", "api"), n("s2", "api"), n("s3", "api")]
    edges = [
        e("e2", "api", "s1", props={"retry": True, "timeout_ms": 100, "backoff": "exponential"}),
        e("e3", "s1", "s2", props={"retry": True, "timeout_ms": 100, "backoff": "exponential"}),
        e("e4", "s2", "s3", props={"retry": True, "timeout_ms": 100, "backoff": "exponential"}),
    ]
    assert run_rules(catalog, g(nodes, edges))["rel.retry_amplification"] == "WARNING"

    two_edges = edges[:2]
    got = run_rules(catalog, g(nodes, two_edges))
    assert "rel.retry_amplification" not in got


def test_rel_missing_idempotency_on_queue_consumer(catalog):
    graph = g(
        BASE_NODES + [n("q", "kafka", replicas=3), n("w", "worker", replicas=5)],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "w", traffic_type="async_event")],
    )
    assert run_rules(catalog, graph)["rel.missing_idempotency"] == "FAIL"


def test_rel_idempotent_consumer_declared_passes(catalog):
    graph = g(
        BASE_NODES + [n("q", "kafka", replicas=3),
                      n("w", "worker", replicas=5, props={"idempotent_consumer": True})],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "w", traffic_type="async_event")],
    )
    got = run_rules(catalog, graph)
    assert got.get("rel.missing_idempotency") != "FAIL"


def test_rel_queue_without_dlq(catalog):
    graph = g(
        BASE_NODES + [n("q", "rabbitmq"), n("w", "worker", replicas=5,
                                                  props={"idempotent_consumer": True})],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "w", traffic_type="async_event")],
    )
    assert run_rules(catalog, graph)["rel.queue_without_dlq"] == "WARNING"


# ---------------- security ----------------

def test_sec_public_database_direct_client_edge(catalog):
    graph = g(
        [n("c", "client"), n("db", "postgresql", replicas=2)],
        [e("e1", "c", "db")],
    )
    assert run_rules(catalog, graph)["sec.public_database"] == "FAIL"


def test_sec_missing_authentication(catalog):
    graph = g([n("c", "client"), n("api", "api", replicas=2)], [e("e1", "c", "api")])
    assert run_rules(catalog, graph)["sec.missing_authentication"] == "FAIL"


def test_sec_auth_declared_passes(catalog):
    statuses_map = run_rules(catalog, g(BASE_NODES, [e("e1", "c", "api")]))
    assert statuses_map["sec.missing_authentication"] == "PASS"


def test_sec_missing_authorization_multi_user(catalog):
    graph = g(
        [n("c", "client"),
         n("api", "api", replicas=2, props={"auth": True})],
        [e("e1", "c", "api")],
        requirements=[{"id": "u", "description": "users own their documents",
                        "validation_rules": []}],
    )
    assert run_rules(catalog, graph)["sec.missing_authorization"] == "WARNING"


def test_sec_unencrypted_sensitive_flow(catalog):
    graph = g(BASE_NODES, [e("e1", "c", "api", protocol="http")])
    assert run_rules(catalog, graph)["sec.unencrypted_sensitive_flow"] == "WARNING"


def test_sec_encrypted_boundary_passes(catalog):
    graph = g(BASE_NODES, [e("e1", "c", "api", protocol="https")])
    got = run_rules(catalog, graph)
    assert got.get("sec.unencrypted_sensitive_flow") in (None, "PASS")


def test_sec_secrets_embedded_in_properties(catalog):
    node = n("api", "api", replicas=2,
             props={"auth": True, "config": "password=hunter2"})
    graph = g([n("c", "client"), node], [e("e1", "c", "api")])
    assert run_rules(catalog, graph)["sec.missing_secrets_management"] == "WARNING"


def test_sec_secrets_managed_flag_suppresses(catalog):
    node = n("api", "api", replicas=2,
             props={"auth": True, "secrets_managed": True, "config": "password=x"})
    graph = g([n("c", "client"), node], [e("e1", "c", "api")])
    got = run_rules(catalog, graph)
    assert got.get("sec.missing_secrets_management") != "WARNING"


# ---------------- observability ----------------

OBS_PROPS = {"metrics": True, "logs": True, "tracing": True, "alerts": True}


def test_obs_no_metrics(catalog):
    graph = g([n("c", "client"), n("api", "api", replicas=2)], [e("e1", "c", "api")])
    assert run_rules(catalog, graph)["obs.no_metrics"] == "WARNING"


def test_obs_no_logs(catalog):
    graph = g([n("c", "client"), n("api", "api", replicas=2, props={"metrics": True})],
              [e("e1", "c", "api")])
    assert run_rules(catalog, graph)["obs.no_logs"] == "WARNING"


def test_obs_no_tracing_multihop(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2, props={"metrics": True, "logs": True}),
         n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
    )
    assert run_rules(catalog, graph)["obs.no_tracing"] == "WARNING"


def test_obs_alerts_required_for_high_availability_target(catalog):
    graph = g(
        [n("c", "client"),
         n("api", "api", replicas=2, multi_az=True, failover="automatic",
           props={"metrics": True, "logs": True, "tracing": True}),
         n("db", "postgresql", replicas=2, multi_az=True, failover="automatic")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        requirements=[{"id": "ha", "category": "reliability", "description": "stays up",
                        "validation_rules": ["availability >= 99.95"]}],
    )
    assert run_rules(catalog, graph)["obs.no_alerts_critical"] == "FAIL"


def test_obs_full_stack_passes(catalog):
    graph = g([n("c", "client"), n("api", "api", replicas=2, props=dict(OBS_PROPS))],
              [e("e1", "c", "api")])
    got = run_rules(catalog, graph)
    for rule in ("obs.no_metrics", "obs.no_logs"):
        assert got.get(rule) in (None, "PASS")


# ---------------- edge semantics ----------------

def test_edge_cache_not_inline(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("redis", "redis", replicas=2),
         n("db", "postgresql", replicas=2)],
        [e("e1", "c", "api"), e("e2", "api", "db")],  # cache floating unconnected
    )
    assert run_rules(catalog, graph)["edge.cache_not_inline"] == "WARNING"


def test_edge_queue_unconsumed(catalog):
    graph = g(BASE_NODES + [n("k", "kafka", replicas=3)],
              [e("e1", "c", "api"), e("e2", "api", "k", traffic_type="async_event")])
    assert run_rules(catalog, graph)["edge.queue_unconsumed"] == "FAIL"


def test_edge_cdn_unused_static(catalog):
    graph = g(BASE_NODES + [n("cdn", "cdn")], [e("e1", "c", "api")])  # cdn disconnected
    assert run_rules(catalog, graph)["edge.cdn_unused_static"] == "WARNING"


def test_edge_cdn_used_passes(catalog):
    graph = g(BASE_NODES + [n("cdn", "cdn")], [e("e1", "c", "cdn"), e("e2", "c", "api")])
    got = run_rules(catalog, graph)
    assert got.get("edge.cdn_unused_static") in (None, "PASS")


def test_edge_missing_traffic_type_detected_from_raw(catalog):
    from app.evaluation.rules import r_edge_missing_traffic_type
    from tests.eval_helpers import make_ctx

    graph = g([n("c", "client"), n("a", "api")], [e("e1", "c", "a")])
    graph["_raw_edges"] = [{"id": "e1", "source": "c", "target": "a"}]
    results = r_edge_missing_traffic_type(make_ctx(graph, catalog))
    assert results and results[0]["status"] == "WARNING"
