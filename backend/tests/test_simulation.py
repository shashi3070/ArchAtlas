"""Tests for the simulation engine and API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.content.loader import load_catalog
from app.main import create_app
from app.simulation.engine import simulate
from app.simulation.models import (
    NodeOverrides,
    SimulationInput,
    SimulationResult,
    SimulationRun,
    TrafficModel,
    compute_graph_hash,
)

# Load catalog once at module level for all tests
CATALOG = load_catalog()


# ── Shared fixtures ─────────────────────────────────────────────────────────

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
            "id": "lb-1",
            "type": "load_balancer",
            "name": "L7 LB",
            "technology": "nginx",
            "position": {"x": 200, "y": 0},
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
            "position": {"x": 400, "y": 0},
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
            "position": {"x": 600, "y": -100},
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
            "position": {"x": 600, "y": 100},
            "properties": {},
            "capacity": {},
            "availability": {},
            "deployment": {},
            "metadata": {},
        },
    ],
    "edges": [
        {"id": "e1", "source": "client-1", "target": "lb-1", "direction": "unidirectional", "protocol": "http", "traffic_type": "sync_request", "properties": {}},
        {"id": "e2", "source": "lb-1", "target": "api-1", "direction": "unidirectional", "protocol": "http", "traffic_type": "sync_request", "properties": {}},
        {"id": "e3", "source": "api-1", "target": "redis-1", "direction": "unidirectional", "protocol": "tcp", "traffic_type": "sync_request", "properties": {}},
        {"id": "e4", "source": "api-1", "target": "pg-1", "direction": "unidirectional", "protocol": "tcp", "traffic_type": "sync_request", "properties": {}},
    ],
    "groups": [],
    "requirements": [],
    "constraints": [],
    "traffic_model": {},
    "deployment_model": {},
    "metadata": {},
}

OVERLOADED_GRAPH: dict = {
    "nodes": [
        {
            "id": "client-1",
            "type": "client",
            "name": "Users",
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
            "name": "API",
            "technology": "node",
            "position": {"x": 200, "y": 0},
            "properties": {},
            "capacity": {},
            "availability": {"replicas": 1},
            "deployment": {},
            "metadata": {},
        },
        {
            "id": "db-1",
            "type": "postgresql",
            "name": "DB",
            "technology": "postgres",
            "position": {"x": 400, "y": 0},
            "properties": {},
            "capacity": {},
            "availability": {},
            "deployment": {},
            "metadata": {},
        },
    ],
    "edges": [
        {"id": "e1", "source": "client-1", "target": "api-1", "direction": "unidirectional", "protocol": "http", "traffic_type": "sync_request", "properties": {}},
        {"id": "e2", "source": "api-1", "target": "db-1", "direction": "unidirectional", "protocol": "tcp", "traffic_type": "sync_request", "properties": {}},
    ],
    "groups": [],
    "requirements": [],
    "constraints": [],
    "traffic_model": {},
    "deployment_model": {},
    "metadata": {},
}


def _make_input(graph: dict, rps: float, **kw) -> SimulationInput:
    traffic = TrafficModel(total_rps=rps, **kw)
    return SimulationInput(graph_json=graph, traffic=traffic)


# ── Engine unit tests ───────────────────────────────────────────────────────

class TestSimulationEngine:
    def test_returns_result(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 100), CATALOG)
        assert isinstance(result, SimulationResult)
        assert len(result.nodes) > 0
        assert len(result.edges) > 0

    def test_summary_has_totals(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 100), CATALOG)
        assert result.summary.total_rps == 100
        assert result.summary.end_to_end.p50_ms > 0
        assert result.summary.end_to_end.p95_ms >= result.summary.end_to_end.p50_ms
        assert result.summary.end_to_end.p99_ms >= result.summary.end_to_end.p95_ms

    def test_cost_is_positive(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 1000), CATALOG)
        assert result.summary.total_cost.total_usd_per_month > 0

    def test_overloaded_detected(self):
        result = simulate(_make_input(OVERLOADED_GRAPH, 50000), CATALOG)
        assert len(result.summary.overloaded_nodes) > 0
        assert len(result.summary.warnings) > 0

    def test_node_latency_increases_with_utilization(self):
        low = simulate(_make_input(SIMPLE_GRAPH, 100), CATALOG)
        high = simulate(_make_input(SIMPLE_GRAPH, 5000), CATALOG)
        low_api = next((n for n in low.nodes if n.node_type == "api"), None)
        high_api = next((n for n in high.nodes if n.node_type == "api"), None)
        assert low_api is not None and high_api is not None
        assert high_api.latency.p95_ms >= low_api.latency.p95_ms

    def test_deterministic(self):
        inp = _make_input(SIMPLE_GRAPH, 1000)
        r1 = simulate(inp, CATALOG)
        r2 = simulate(inp, CATALOG)
        assert r1.summary.end_to_end.p95_ms == r2.summary.end_to_end.p95_ms
        assert r1.summary.total_cost.total_usd_per_month == r2.summary.total_cost.total_usd_per_month

    def test_cache_reduces_effective_rps(self):
        inp = _make_input(SIMPLE_GRAPH, 1000)
        result = simulate(inp, CATALOG)
        assert result.summary.effective_rps <= result.summary.total_rps

    def test_node_result_fields(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 1000), CATALOG)
        for node in result.nodes:
            assert node.node_id
            assert node.node_type
            assert node.capacity_rps >= 0
            assert node.offered_rps >= 0
            assert 0 <= node.error_rate <= 1
            assert node.latency.p50_ms > 0
            assert node.cost.usd_per_month >= 0

    def test_edge_result_fields(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 1000), CATALOG)
        for edge in result.edges:
            assert edge.edge_id
            assert edge.source
            assert edge.target
            assert edge.flow.rps >= 0
            assert edge.flow.bandwidth_mbps >= 0

    def test_input_hash_deterministic(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 100), CATALOG)
        assert result.input_hash
        assert len(result.input_hash) == 16

    def test_trace_paths_non_empty(self):
        result = simulate(_make_input(SIMPLE_GRAPH, 1000), CATALOG)
        assert len(result.trace_paths) > 0

    def test_node_overrides_apply(self):
        inp = _make_input(SIMPLE_GRAPH, 1000)
        inp.node_overrides = [NodeOverrides(node_id="api-1", replicas=10)]
        result = simulate(inp, CATALOG)
        api_node = next(n for n in result.nodes if n.node_id == "api-1")
        assert api_node.capacity_rps > 0

    def test_graph_hash(self):
        h = compute_graph_hash(SIMPLE_GRAPH)
        assert isinstance(h, str)
        assert len(h) == 16

    def test_traffic_ratio_validation(self):
        with pytest.raises(ValueError, match="must sum to ~1.0"):
            TrafficModel(total_rps=100, read_ratio=0.7, write_ratio=0.7)


# ── API tests ───────────────────────────────────────────────────────────────

class TestSimulationAPI:
    @pytest.fixture(autouse=True)
    def _client(self):
        app = create_app()
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_post_simulate(self):
        payload = {
            "graph_json": SIMPLE_GRAPH,
            "traffic": {"total_rps": 1000},
        }
        resp = self.client.post("/api/simulate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "nodes" in body
        assert "summary" in body

    def test_post_simulate_validation(self):
        resp = self.client.post("/api/simulate", json={"graph_json": {}, "traffic": {"total_rps": -1}})
        assert resp.status_code == 422

    def test_quick_simulate(self):
        resp = self.client.post("/api/simulate/quick", params={"total_rps": 500}, json=SIMPLE_GRAPH)
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total_rps"] == 500

    def test_list_runs(self):
        # First run something to populate the store
        self.client.post("/api/simulate", json={"graph_json": SIMPLE_GRAPH, "traffic": {"total_rps": 100}})
        resp = self.client.get("/api/simulate")
        assert resp.status_code == 200
        runs = resp.json()
        assert isinstance(runs, list)

    def test_get_run_not_found(self):
        resp = self.client.get("/api/simulate/nonexistent")
        assert resp.status_code == 404
