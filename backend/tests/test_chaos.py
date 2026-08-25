"""Tests for chaos engineering events and API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.chaos.events import (
    EVENTS,
    apply_chaos_event,
    build_delta_report,
    get_event,
    list_events,
    run_chaos,
)
from app.chaos.models import ChaosEventType, ChaosRunResult, DeltaReport
from app.content.loader import load_catalog
from app.main import create_app
from app.simulation.models import SimulationInput, TrafficModel, compute_graph_hash

CATALOG = load_catalog()

SIMPLE_GRAPH: dict = {
    "nodes": [
        {
            "id": "client-1",
            "type": "client",
            "name": "Web Client",
            "technology": None,
            "position": {"x": 0, "y": 0},
            "properties": {},
            "capacity": {},
            "availability": {},
            "deployment": {},
            "metadata": {},
        },
        {
            "id": "api-1",
            "type": "api",
            "name": "API Gateway",
            "technology": "fastapi",
            "position": {"x": 200, "y": 0},
            "properties": {},
            "capacity": {},
            "availability": {"replicas": 3},
            "deployment": {},
            "metadata": {},
        },
        {
            "id": "redis-1",
            "type": "redis",
            "name": "Redis Cache",
            "technology": "redis",
            "position": {"x": 400, "y": -100},
            "properties": {},
            "capacity": {},
            "availability": {},
            "deployment": {},
            "metadata": {},
        },
        {
            "id": "pg-1",
            "type": "postgresql",
            "name": "Primary DB",
            "technology": "postgresql",
            "position": {"x": 400, "y": 100},
            "properties": {},
            "capacity": {},
            "availability": {},
            "deployment": {},
            "metadata": {},
        },
    ],
    "edges": [
        {"id": "e1", "source": "client-1", "target": "api-1", "direction": "unidirectional", "protocol": "http", "traffic_type": "sync_request", "properties": {}},
        {"id": "e2", "source": "api-1", "target": "redis-1", "direction": "unidirectional", "protocol": "tcp", "traffic_type": "sync_request", "properties": {}},
        {"id": "e3", "source": "api-1", "target": "pg-1", "direction": "unidirectional", "protocol": "tcp", "traffic_type": "sync_request", "properties": {}},
    ],
    "groups": [],
    "requirements": [],
    "constraints": [],
    "traffic_model": {"rps": 1000},
    "deployment_model": {},
    "metadata": {},
}


# ── Event library tests ─────────────────────────────────────────────────────

class TestChaosEvents:
    def test_list_events_has_ten(self):
        events = list_events()
        assert len(events) == 10

    def test_all_event_types_covered(self):
        listed = {e.id for e in EVENTS}
        for et in ChaosEventType:
            assert et in listed, f"Missing event: {et}"

    def test_get_event(self):
        e = get_event(ChaosEventType.DB_FAILURE)
        assert e.name == "Database Primary Failure"
        assert "postgresql" in e.affected_node_types

    def test_get_event_unknown(self):
        with pytest.raises(ValueError, match="Unknown event"):
            get_event("nonexistent")  # type: ignore[arg-type]


# ── Graph injection tests ───────────────────────────────────────────────────

class TestChaosInjection:
    def test_db_failure_sets_replicas_zero(self):
        event = get_event(ChaosEventType.DB_FAILURE)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event)
        pg_node = next(n for n in chaos_graph["nodes"] if n["id"] == "pg-1")
        assert pg_node["availability"]["replicas"] == 0

    def test_cache_failure_sets_hit_ratio_zero(self):
        event = get_event(ChaosEventType.CACHE_FAILURE)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event)
        redis_node = next(n for n in chaos_graph["nodes"] if n["id"] == "redis-1")
        assert redis_node["capacity"]["default_hit_ratio_assumption"] == 0.0

    def test_traffic_spike_multiplies_rps(self):
        event = get_event(ChaosEventType.TRAFFIC_SPIKE)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event)
        assert chaos_graph["traffic_model"]["rps"] == 10000

    def test_network_latency_adds_ms(self):
        event = get_event(ChaosEventType.NETWORK_LATENCY)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event, catalog=CATALOG)
        api_node = next(n for n in chaos_graph["nodes"] if n["id"] == "api-1")
        # Base from catalog is 50ms, plus 200ms injected = 250ms
        assert api_node["capacity"]["p95_base_ms"] == 250.0

    def test_hit_ratio_drop(self):
        event = get_event(ChaosEventType.HIT_RATIO_DROP)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event)
        redis_node = next(n for n in chaos_graph["nodes"] if n["id"] == "redis-1")
        assert redis_node["capacity"]["default_hit_ratio_assumption"] == 0.20

    def test_does_not_mutate_original(self):
        original = compute_graph_hash(SIMPLE_GRAPH)
        event = get_event(ChaosEventType.DB_FAILURE)
        apply_chaos_event(SIMPLE_GRAPH, event)
        assert compute_graph_hash(SIMPLE_GRAPH) == original

    def test_region_outage_reduces_replicas(self):
        event = get_event(ChaosEventType.REGION_OUTAGE)
        chaos_graph = apply_chaos_event(SIMPLE_GRAPH, event)
        api_node = next(n for n in chaos_graph["nodes"] if n["id"] == "api-1")
        assert api_node["availability"]["replicas"] < 3


# ── Full chaos run tests ────────────────────────────────────────────────────

class TestChaosRun:
    def test_run_db_failure(self):
        result = run_chaos(SIMPLE_GRAPH, ChaosEventType.DB_FAILURE, catalog=CATALOG)
        assert isinstance(result, ChaosRunResult)
        assert result.event_id == ChaosEventType.DB_FAILURE
        assert result.delta_report.availability_after < result.delta_report.availability_before

    def test_run_cache_failure_increases_latency(self):
        result = run_chaos(SIMPLE_GRAPH, ChaosEventType.CACHE_FAILURE, catalog=CATALOG)
        assert result.delta_report.latency_p95_after >= result.delta_report.latency_p95_before

    def test_run_traffic_spike_overloads(self):
        result = run_chaos(SIMPLE_GRAPH, ChaosEventType.TRAFFIC_SPIKE, catalog=CATALOG)
        assert len(result.outcomes) == 1
        assert result.outcomes[0].severity in ("medium", "high", "critical")

    def test_deterministic(self):
        r1 = run_chaos(SIMPLE_GRAPH, ChaosEventType.DB_FAILURE, catalog=CATALOG)
        r2 = run_chaos(SIMPLE_GRAPH, ChaosEventType.DB_FAILURE, catalog=CATALOG)
        assert r1.delta_report.availability_after == r2.delta_report.availability_after
        assert r1.delta_report.latency_p95_after == r2.delta_report.latency_p95_after

    def test_severity_classification(self):
        result = run_chaos(SIMPLE_GRAPH, ChaosEventType.DB_FAILURE, catalog=CATALOG)
        assert result.outcomes[0].severity in ("medium", "high", "critical")

    def test_delta_has_root_cause(self):
        result = run_chaos(SIMPLE_GRAPH, ChaosEventType.CACHE_FAILURE, catalog=CATALOG)
        assert result.delta_report.root_cause
        assert result.delta_report.mitigation


# ── API tests ───────────────────────────────────────────────────────────────

class TestChaosAPI:
    @pytest.fixture(autouse=True)
    def _client(self):
        app = create_app()
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_list_events(self):
        resp = self.client.get("/api/chaos/events")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) == 10

    def test_get_event_detail(self):
        resp = self.client.get("/api/chaos/events/db_failure")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "db_failure"

    def test_get_event_not_found(self):
        resp = self.client.get("/api/chaos/events/nonexistent")
        assert resp.status_code == 404

    def test_run_chaos_event(self):
        resp = self.client.post(
            "/api/chaos/run",
            json={"graph_json": SIMPLE_GRAPH, "event_id": "cache_failure"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "delta_report" in body
        assert body["event_id"] == "cache_failure"

    def test_run_chaos_invalid_event(self):
        resp = self.client.post(
            "/api/chaos/run",
            json={"graph_json": SIMPLE_GRAPH, "event_id": "invalid"},
        )
        assert resp.status_code == 400

    def test_inject_event(self):
        resp = self.client.post(
            "/api/chaos/inject",
            json={"graph_json": SIMPLE_GRAPH, "event_id": "traffic_spike"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["traffic_model"]["rps"] == 10000

    def test_list_runs(self):
        # Run one first
        self.client.post(
            "/api/chaos/run",
            json={"graph_json": SIMPLE_GRAPH, "event_id": "db_failure"},
        )
        resp = self.client.get("/api/chaos/runs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
