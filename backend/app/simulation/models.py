"""Pydantic models for the analytical simulation layer."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# ── Input ────────────────────────────────────────────────────────────────────

class TrafficModel(BaseModel):
    """Traffic assumptions driving the simulation."""

    total_rps: float = Field(..., gt=0, description="Total requests per second")
    read_ratio: float = Field(0.8, ge=0, le=1, description="Fraction of traffic that is reads (0–1)")
    write_ratio: float = Field(0.2, ge=0, le=1, description="Fraction of traffic that is writes (0–1)")
    avg_request_bytes: float = Field(2048, gt=0, description="Average request payload size in bytes")
    avg_response_bytes: float = Field(8192, gt=0, description="Average response payload size in bytes")
    avg_data_record_bytes: float = Field(1024, gt=0, description="Average data record size in bytes")
    think_time_ms: float = Field(0, ge=0, description="Client think time between requests (ms)")

    def model_post_init(self, _context: object) -> None:
        total = self.read_ratio + self.write_ratio
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"read_ratio ({self.read_ratio}) + write_ratio ({self.write_ratio}) "
                f"must sum to ~1.0 (got {total})"
            )


class NodeOverrides(BaseModel):
    """Per-node overrides for a single simulation run."""

    node_id: str
    replicas: int | None = None
    cache_hit_ratio: float | None = None
    properties: dict[str, object] = Field(default_factory=dict)


class SimulationInput(BaseModel):
    """Complete input for a simulation run."""

    graph_json: dict = Field(..., description="Canonical architecture graph (full dict)")
    traffic: TrafficModel
    node_overrides: list[NodeOverrides] = Field(default_factory=list)


# ── Per-node result ──────────────────────────────────────────────────────────

class NodeUtilization(BaseModel):
    read_utilization: float = Field(0, ge=0, description="Fraction of read capacity used (0–1, >1 = overloaded)")
    write_utilization: float = Field(0, ge=0, description="Fraction of write capacity used")
    total_utilization: float = Field(0, ge=0, description="Combined utilization")

    @property
    def is_overloaded(self) -> bool:
        return self.total_utilization > 1.0

    @property
    def is_critical(self) -> bool:
        return 0.8 <= self.total_utilization <= 1.0


class NodeLatency(BaseModel):
    p50_ms: float = Field(0, ge=0)
    p95_ms: float = Field(0, ge=0)
    p99_ms: float = Field(0, ge=0)
    base_ms: float = Field(0, ge=0, description="Base processing latency before queueing")


class NodeCost(BaseModel):
    usd_per_month: float = Field(0, ge=0)
    usd_per_request: float = Field(0, ge=0)


class NodeSimulationResult(BaseModel):
    node_id: str
    node_type: str
    name: str

    capacity_rps: float = Field(0, description="Node throughput capacity (reads, writes, or combined)")
    offered_rps: float = Field(0, description="RPS actually hitting this node")
    routed_rps: float = Field(0, description="RPS successfully processed")

    utilization: NodeUtilization
    latency: NodeLatency
    cost: NodeCost

    error_rate: float = Field(0, ge=0, le=1, description="Estimated error rate due to saturation")
    queue_depth: float = Field(0, ge=0, description="Estimated steady-state queue depth")
    is_bottleneck: bool = False
    warnings: list[str] = Field(default_factory=list)


# ── Per-edge result ──────────────────────────────────────────────────────────

class EdgeFlow(BaseModel):
    rps: float = Field(0, description="Traffic flow on this edge (RPS)")
    bandwidth_mbps: float = Field(0, ge=0, description="Bandwidth in Mbps")
    saturation: float = Field(0, ge=0, le=1, description="Edge saturation 0–1")

    @property
    def visual_weight(self) -> float:
        """Thickness factor for canvas overlay (0–1 normalized to max edge)."""
        return min(self.saturation * 1.2, 1.0)


class EdgeSimulationResult(BaseModel):
    edge_id: str
    source: str
    target: str
    traffic_type: str

    flow: EdgeFlow
    warnings: list[str] = Field(default_factory=list)


# ── Aggregate results ────────────────────────────────────────────────────────

class TrafficPath(BaseModel):
    """One trace path (e.g. Client → LB → API → Redis → DB)."""

    path_nodes: list[str]
    total_latency_ms: float
    hops: list[TrafficHop]


class TrafficHop(BaseModel):
    node_id: str
    node_type: str
    latency_ms: float
    cache_hit: bool = False
    queued: bool = False


class PercentileEstimate(BaseModel):
    p50_ms: float
    p95_ms: float
    p99_ms: float


# ── Simulation result ────────────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    total_usd_per_month: float = 0
    per_node_usd_per_month: dict[str, float] = Field(default_factory=dict)


class SimulationSummary(BaseModel):
    """High-level summary of the simulation."""

    total_rps: float
    effective_rps: float = Field(..., description="RPS after cache hits reduce DB load")
    end_to_end: PercentileEstimate
    total_cost: CostBreakdown
    bottleneck_node: str | None = None
    overloaded_nodes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Complete output of a simulation run."""

    input_hash: str
    nodes: list[NodeSimulationResult]
    edges: list[EdgeSimulationResult]
    trace_paths: list[TrafficPath] = Field(default_factory=list)
    summary: SimulationSummary
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Persistence model ────────────────────────────────────────────────────────

class SimulationRun(BaseModel):
    """Saved simulation run for comparison and history."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    owner_key: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    architecture_id: str | None = None
    architecture_version: int | None = None
    graph_hash: str
    traffic_rps: float
    input_json: dict
    result_json: dict
    result_summary: str = ""


def compute_graph_hash(graph: dict) -> str:
    """Deterministic SHA-256 of the graph for caching / comparison."""
    stable = json.dumps(graph, sort_keys=True, default=str)
    return hashlib.sha256(stable.encode()).hexdigest()[:16]
