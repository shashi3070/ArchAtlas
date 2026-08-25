"""Pydantic models for chaos engineering events and runs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChaosEventType(str, Enum):
    """Catalog of injectable failure scenarios."""

    DB_FAILURE = "db_failure"
    CACHE_FAILURE = "cache_failure"
    QUEUE_FAILURE = "queue_failure"
    REGION_OUTAGE = "region_outage"
    NETWORK_LATENCY = "network_latency"
    TRAFFIC_SPIKE = "traffic_spike"
    HOT_KEY = "hot_key"
    CONSUMER_LAG = "consumer_lag"
    DEPENDENCY_OUTAGE = "dependency_outage"
    HIT_RATIO_DROP = "hit_ratio_drop"


class ChaosEvent(BaseModel):
    """Definition of a single chaos event."""

    id: ChaosEventType
    name: str
    description: str
    affected_node_types: list[str]
    transform: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph transforms applied: replica_mul, capacity_mul, latency_add_ms, hit_ratio_set, remove_edge_ids, add_latency_edges",
    )
    expected_effect: str = Field(
        "",
        description="Human-readable expected effect description",
    )


class EventOutcome(BaseModel):
    """Result of injecting one event."""

    event_id: ChaosEventType
    event_name: str
    affected_node_ids: list[str]
    before_summary: dict[str, Any] = Field(default_factory=dict)
    after_summary: dict[str, Any] = Field(default_factory=dict)
    delta: dict[str, Any] = Field(default_factory=dict)
    severity: str = "unknown"  # low, medium, high, critical


class DeltaReport(BaseModel):
    """Before/after comparison across all simulation metrics."""

    availability_before: float = 0
    availability_after: float = 0
    latency_p95_before: float = 0
    latency_p95_after: float = 0
    cost_before: float = 0
    cost_after: float = 0
    error_rate_before: float = 0
    error_rate_after: float = 0
    overloaded_nodes_before: list[str] = Field(default_factory=list)
    overloaded_nodes_after: list[str] = Field(default_factory=list)
    bottleneck_before: str | None = None
    bottleneck_after: str | None = None
    root_cause: str = ""
    mitigation: str = ""


class ChaosRunResult(BaseModel):
    """Complete output of a chaos simulation run."""

    event_id: ChaosEventType
    event_name: str
    before_simulation: dict[str, Any] = Field(default_factory=dict)
    after_simulation: dict[str, Any] = Field(default_factory=dict)
    delta_report: DeltaReport
    outcomes: list[EventOutcome] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChaosRun(BaseModel):
    """Saved chaos run for comparison and history."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    owner_key: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    architecture_id: str | None = None
    event_id: str
    graph_hash: str = ""
    result_json: dict[str, Any] = Field(default_factory=dict)
    result_summary: str = ""
