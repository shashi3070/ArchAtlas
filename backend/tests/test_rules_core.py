"""Rule-level tests: graph + scale categories. Parametrized trigger/pass cases."""

from __future__ import annotations

from tests.eval_helpers import CLIENT_LB_API_DB, e, g, n, run_rules

# ---------------- graph ----------------

def test_graph_no_ingress_triggers_without_client(catalog):
    graph = g([n("api", "api", replicas=2)], [])
    assert run_rules(catalog, graph)["graph.no_ingress"] == "FAIL"


def test_graph_no_ingress_passes_on_connected_path(catalog):
    statuses_map = run_rules(catalog, CLIENT_LB_API_DB)
    assert statuses_map.get("graph.no_ingress", "PASS") == "PASS"


def test_graph_missing_source_and_destination(catalog):
    graph = g(
        [n("a", "api"), n("db", "postgresql")],
        [e("e1", "ghost", "a"), e("e2", "db", "phantom")],
    )
    got = run_rules(catalog, graph)
    assert got["graph.missing_source"] == "FAIL"
    assert got["graph.missing_destination"] == "FAIL"


def test_graph_invalid_edge_self_loop(catalog):
    graph = g([n("a", "api")], [e("e1", "a", "a")])
    assert run_rules(catalog, graph)["graph.invalid_edge"] == "FAIL"


def test_graph_inappropriate_cycle_sync(catalog):
    graph = g(
        [n("c", "client"), n("a", "api"), n("b", "worker")],
        [e("e1", "c", "a"), e("e2", "a", "b"), e("e3", "b", "a")],
    )
    got = run_rules(catalog, graph)
    # a -> b -> a is a sync cycle (default traffic type).
    assert got.get("graph.inappropriate_cycle", "PASS") in ("WARNING",)


def test_graph_cycle_allowed_for_async(catalog):
    graph = g(
        [n("c", "client"), n("k", "kafka"), n("w", "worker")],
        [
            e("e1", "c", "k", traffic_type="async_event"),
            e("e2", "k", "w", traffic_type="async_event"),
            e("e3", "w", "k", traffic_type="async_event"),
        ],
    )
    got = run_rules(catalog, graph)
    assert "graph.inappropriate_cycle" not in got or got["graph.inappropriate_cycle"] == "PASS"


def test_graph_no_data_store_required_when_requirement_mentions_store(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2, props={"auth": True})],
        [e("e1", "c", "api")],
        requirements=[
            {"id": "r1", "category": "functional",
             "description": "sessions must be stored persistently",
             "validation_rules": []}
        ],
    )
    assert run_rules(catalog, graph)["graph.no_data_store_required"] == "FAIL"


def test_graph_data_store_satisfies_persistence_requirement(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("db", "postgresql")],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        requirements=[
            {"id": "r1", "description": "data must be stored", "validation_rules": []}
        ],
    )
    assert run_rules(catalog, graph)["graph.no_data_store_required"] == "PASS"


# ---------------- scale ----------------

HIGH_TRAFFIC = {"traffic_model": {"rps": 50000, "read_ratio": 0.8}}


def test_scale_single_compute_high_traffic_fails_small_tier(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=1)],
        [e("e1", "c", "api")],
        **HIGH_TRAFFIC,
    )
    assert run_rules(catalog, graph)["scale.single_compute_high_traffic"] == "FAIL"


def test_scale_capacity_passes_with_enough_replicas(catalog):
    graph = g(
        [n("c", "client"),
         n("api", "api", replicas=60, capacity={"rps_per_instance": 1000})],
        [e("e1", "c", "api")],
        **HIGH_TRAFFIC,
    )
    assert run_rules(catalog, graph)["scale.single_compute_high_traffic"] == "PASS"


def test_scale_unknown_demand_is_unknown(catalog):
    graph = g([n("c", "client"), n("api", "api", replicas=1)], [e("e1", "c", "api")])
    assert run_rules(catalog, graph)["scale.single_compute_high_traffic"] == "UNKNOWN"


def test_scale_db_write_bottleneck(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=10),
         n("db", "mongodb", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        traffic_model={"rps": 200000, "write_ratio": 0.9},
    )
    assert run_rules(catalog, graph)["scale.db_write_bottleneck"] == "FAIL"


def test_scale_db_write_ok_with_shards_and_queue(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=10),
         n("q", "kafka", replicas=3),
         n("db", "mongodb", replicas=1, avail={"shards": 16})],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event"),
         e("e3", "q", "api", traffic_type="async_event")],
        traffic_model={"rps": 100000, "write_ratio": 0.9},
    )
    # 90k/s writes vs 16 shards x 8000 safe = 128k -> no violation emitted.
    got = run_rules(catalog, graph).get("scale.db_write_bottleneck", "PASS")
    assert got != "FAIL"


def test_scale_db_read_bottleneck_without_cache(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=5),
         n("db", "postgresql", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "db")],
        traffic_model={"rps": 50000, "read_ratio": 0.95},
    )
    assert run_rules(catalog, graph)["scale.db_read_bottleneck"] == "FAIL"


def test_scale_db_reads_absorbed_by_inline_cache(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=5),
         n("redis", "redis", replicas=2),
         n("db", "postgresql", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "redis"), e("e3", "redis", "db")],
        traffic_model={"rps": 50000, "read_ratio": 0.95},
    )
    got = run_rules(catalog, graph).get("scale.db_read_bottleneck", "PASS")
    assert got != "FAIL"


def test_scale_worker_capacity_fail(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("q", "rabbitmq", replicas=2),
         n("w", "worker", replicas=1)],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="batch"),
         e("e3", "q", "w", traffic_type="batch")],
        traffic_model={"rps": 10000, "write_ratio": 0.5},
    )
    assert run_rules(catalog, graph)["scale.insufficient_worker_capacity"] == "FAIL"


def test_scale_worker_capacity_pass(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("q", "rabbitmq", replicas=2),
         n("w", "worker", replicas=150)],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="batch"),
         e("e3", "q", "w", traffic_type="batch")],
        traffic_model={"rps": 10000, "write_ratio": 0.5},
    )
    got = run_rules(catalog, graph)["scale.insufficient_worker_capacity"]
    assert got == "PASS"


def test_scale_queue_consumer_shortage(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2), n("q", "kafka", replicas=3)],
        [e("e1", "c", "api"), e("e2", "api", "q", traffic_type="async_event")],
    )
    got = run_rules(catalog, graph)
    assert got["edge.queue_unconsumed"] == "FAIL"
    assert got["scale.queue_consumer_shortage"] == "FAIL"


def test_scale_partition_hot_spot_single_shard(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=2),
         n("mongo", "mongodb", replicas=2, props={"shards": 1})],
        [e("e1", "c", "api"), e("e2", "api", "mongo")],
    )
    assert run_rules(catalog, graph)["scale.partition_hot_spot"] == "WARNING"


def test_scale_missing_load_balancing_multiple_apis(catalog):
    graph = g(
        [n("c", "client"), n("a1", "api", replicas=2), n("a2", "api", replicas=2)],
        [e("e1", "c", "a1")],
    )
    assert run_rules(catalog, graph)["scale.missing_load_balancing"] == "WARNING"


def test_scale_lb_present_satisfies_distribution(catalog):
    statuses_map = run_rules(catalog, CLIENT_LB_API_DB)
    assert "scale.missing_load_balancing" not in statuses_map or \
        statuses_map["scale.missing_load_balancing"] == "PASS"


def test_scale_missing_horizontal_scaling(catalog):
    graph = g(
        [n("c", "client"), n("api", "api", replicas=1)],
        [e("e1", "c", "api")],
        **HIGH_TRAFFIC,
    )
    assert run_rules(catalog, graph)["scale.missing_horizontal_scaling"] == "FAIL"
