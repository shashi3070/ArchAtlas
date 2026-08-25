"""Chaos event definitions, graph injection, and delta report builder.

Pure, deterministic — no I/O. Same input always produces same output.
"""

from __future__ import annotations

import copy
from typing import Any

from app.chaos.models import (
    ChaosEvent,
    ChaosEventType,
    ChaosRunResult,
    DeltaReport,
    EventOutcome,
)
from app.simulation.engine import simulate
from app.simulation.models import SimulationInput, TrafficModel


# ── Event library ────────────────────────────────────────────────────────────

EVENTS: list[ChaosEvent] = [
    ChaosEvent(
        id=ChaosEventType.DB_FAILURE,
        name="Database Primary Failure",
        description="The primary database node becomes unavailable. Replicas may promote if configured.",
        affected_node_types=["postgresql", "mysql", "mongodb", "cockroachdb", "spanner", "dynamodb", "cassandra"],
        transform={"replica_mul": 0},
        expected_effect="Availability drops significantly if no automatic failover. Read capacity drops to zero for writes.",
    ),
    ChaosEvent(
        id=ChaosEventType.CACHE_FAILURE,
        name="Cache Layer Failure",
        description="All cache nodes (Redis/Memcached) become unavailable. 100% of reads fall through to database.",
        affected_node_types=["redis", "memcached"],
        transform={"replica_mul": 0, "hit_ratio_set": 0.0},
        expected_effect="Database read load increases dramatically (10x typical). Latency spikes. Possible DB overload.",
    ),
    ChaosEvent(
        id=ChaosEventType.QUEUE_FAILURE,
        name="Message Queue Failure",
        description="Queue brokers (Kafka/RabbitMQ/SQS) become unavailable. Producers may block or drop events.",
        affected_node_types=["kafka", "rabbitmq", "sqs", "pubsub", "nats", "kinesis", "event_bus"],
        transform={"replica_mul": 0},
        expected_effect="Async processing halts. Events pile up or are lost. Downstream consumers starve.",
    ),
    ChaosEvent(
        id=ChaosEventType.REGION_OUTAGE,
        name="Entire Region Outage",
        description="One availability zone goes down. All nodes in that zone fail.",
        affected_node_types=["*"],
        transform={"region_fraction": 0.33},
        expected_effect="Capacity reduced by ~33%. Remaining nodes may become overloaded. Cross-AZ latency increases.",
    ),
    ChaosEvent(
        id=ChaosEventType.NETWORK_LATENCY,
        name="Network Latency Injection",
        description="Adds 200ms latency to all inter-node communication.",
        affected_node_types=["*"],
        transform={"latency_add_ms": 200},
        expected_effect="P95 latency increases significantly. Timeout cascades possible. Throughput may drop.",
    ),
    ChaosEvent(
        id=ChaosEventType.TRAFFIC_SPIKE,
        name="10x Traffic Spike",
        description="Incoming traffic increases 10x instantly.",
        affected_node_types=["client"],
        transform={"traffic_mul": 10},
        expected_effect="All downstream nodes overloaded. Queue depths grow. Error rates spike. Cost increases.",
    ),
    ChaosEvent(
        id=ChaosEventType.HOT_KEY,
        name="Hot Key / Hot Partition",
        description="One data key receives 100x normal traffic, overwhelming cache and DB.",
        affected_node_types=["redis", "postgresql", "mongodb"],
        transform={"hot_key_factor": 100},
        expected_effect="Single-node hotspot. Cache stampede. DB query queue fills. Latency variance increases.",
    ),
    ChaosEvent(
        id=ChaosEventType.CONSUMER_LAG,
        name="Consumer Lag Surge",
        description="Queue consumers slow down 10x, causing message backlog.",
        affected_node_types=["worker", "kafka", "rabbitmq"],
        transform={"consumer_slowdown": 10},
        expected_effect="Queue depth grows. Event processing delayed. Downstream data becomes stale.",
    ),
    ChaosEvent(
        id=ChaosEventType.DEPENDENCY_OUTAGE,
        name="External Dependency Outage",
        description="A downstream API or third-party service becomes unavailable.",
        affected_node_types=["api", "cdn"],
        transform={"replica_mul": 0},
        expected_effect="Requests to dependency fail. Circuit breaker trips. Error rate increases.",
    ),
    ChaosEvent(
        id=ChaosEventType.HIT_RATIO_DROP,
        name="Cache Hit Ratio Collapse",
        description="Cache hit ratio drops from 90% to 20% due to pattern change or cache invalidation.",
        affected_node_types=["redis", "memcached"],
        transform={"hit_ratio_set": 0.20},
        expected_effect="Database read load increases 4-7x. Latency increases. Possible DB overload at high RPS.",
    ),
]


def list_events() -> list[ChaosEvent]:
    """Return all available chaos events."""
    return EVENTS


def get_event(event_id: ChaosEventType) -> ChaosEvent:
    """Get a single event by ID."""
    for e in EVENTS:
        if e.id == event_id:
            return e
    raise ValueError(f"Unknown event: {event_id}")


# ── Graph injection ──────────────────────────────────────────────────────────

def _apply_replica_mul(graph: dict, fraction: float) -> dict:
    """Reduce replicas for all nodes matching affected types."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        avail = node.get("availability") or {}
        replicas = avail.get("replicas", 1)
        if fraction == 0:
            avail["replicas"] = 0
        else:
            avail["replicas"] = max(0, int(replicas * fraction))
        node["availability"] = avail
    return g


def _apply_region_fraction(graph: dict, fraction: float) -> dict:
    """Simulate region outage by reducing all replicas proportionally."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        avail = node.get("availability") or {}
        replicas = avail.get("replicas", 1)
        avail["replicas"] = max(1, int(replicas * (1 - fraction)))
        node["availability"] = avail
    return g


def _apply_latency_add(graph: dict, add_ms: float) -> dict:
    """Add latency to all compute/cache/DB nodes."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        cap = node.get("capacity") or {}
        base = cap.get("p95_base_ms", 1.0)
        cap["p95_base_ms"] = base + add_ms
        node["capacity"] = cap
    return g


def _apply_traffic_mul(graph: dict, multiplier: float) -> dict:
    """Multiply the traffic model RPS."""
    g = copy.deepcopy(graph)
    tm = g.get("traffic_model") or {}
    rps = tm.get("rps", 1000)
    tm["rps"] = rps * multiplier
    g["traffic_model"] = tm
    return g


def _apply_hit_ratio_set(graph: dict, ratio: float) -> dict:
    """Force cache hit ratio to a specific value."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        cap = node.get("capacity") or {}
        cap["default_hit_ratio_assumption"] = ratio
        node["capacity"] = cap
    return g


def _apply_latency_add(graph: dict, add_ms: float, catalog: dict | None = None) -> dict:
    """Add latency to all compute/cache/DB nodes, reading base from catalog if needed."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        cap = node.get("capacity") or {}
        base = cap.get("p95_base_ms")
        if base is None and catalog:
            entry = catalog.get(node.get("type", ""))
            base = ((entry or {}).get("capacity_defaults") or {}).get("p95_base_ms")
        if base is None:
            base = 1.0
        cap["p95_base_ms"] = float(base) + add_ms
        node["capacity"] = cap
    return g


def _apply_hot_key(graph: dict, factor: float) -> dict:
    """Simulate hot key by reducing effective capacity of storage nodes."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        cap = node.get("capacity") or {}
        for key in ("safe_reads_per_sec", "safe_writes_per_sec", "reads_per_sec_per_node"):
            if key in cap:
                cap[key] = cap[key] / factor
        node["capacity"] = cap
    return g


def _apply_consumer_slowdown(graph: dict, slowdown: float) -> dict:
    """Simulate consumer lag by reducing worker/queue throughput."""
    g = copy.deepcopy(graph)
    for node in g.get("nodes", []):
        cap = node.get("capacity") or {}
        for key in ("events_per_sec_per_broker", "rps_per_instance"):
            if key in cap:
                cap[key] = cap[key] / slowdown
        node["capacity"] = cap
    return g


def apply_chaos_event(
    graph: dict,
    event: ChaosEvent,
    traffic_rps: float | None = None,
    catalog: dict | None = None,
) -> dict:
    """
    Apply a chaos event transform to a copy of the graph.

    Returns a new graph dict — never mutates the original.
    """
    t = event.transform

    if "replica_mul" in t:
        g = _apply_replica_mul(graph, t["replica_mul"])
    elif "region_fraction" in t:
        g = _apply_region_fraction(graph, t["region_fraction"])
    else:
        g = copy.deepcopy(graph)

    if "latency_add_ms" in t:
        g = _apply_latency_add(g, t["latency_add_ms"], catalog)

    if "traffic_mul" in t:
        g = _apply_traffic_mul(g, t["traffic_mul"])

    if "hit_ratio_set" in t:
        g = _apply_hit_ratio_set(g, t["hit_ratio_set"])

    if "hot_key_factor" in t:
        g = _apply_hot_key(g, t["hot_key_factor"])

    if "consumer_slowdown" in t:
        g = _apply_consumer_slowdown(g, t["consumer_slowdown"])

    return g


# ── Delta report builder ─────────────────────────────────────────────────────

def _summarize(result_dict: dict) -> dict[str, Any]:
    """Extract key metrics from a SimulationResult dict."""
    summary = result_dict.get("summary", {})
    e2e = summary.get("end_to_end", {})
    cost = summary.get("total_cost", {})
    return {
        "total_rps": summary.get("total_rps", 0),
        "effective_rps": summary.get("effective_rps", 0),
        "p95_ms": e2e.get("p95_ms", 0),
        "p99_ms": e2e.get("p99_ms", 0),
        "cost_monthly": cost.get("total_usd_per_month", 0),
        "overloaded_nodes": summary.get("overloaded_nodes", []),
        "bottleneck": summary.get("bottleneck_node"),
        "warnings": summary.get("warnings", []),
    }


def _estimate_availability(before: dict, after: dict) -> tuple[float, float]:
    """
    Heuristic availability estimate based on overloaded nodes and error rates.
    Baseline 99.95% for healthy; degrades with overload.
    """
    base = 99.95
    before_overloaded = len(before.get("overloaded_nodes", []))
    after_overloaded = len(after.get("overloaded_nodes", []))
    b_avail = base * (1 - before_overloaded * 0.05)
    a_avail = base * (1 - after_overloaded * 0.10)
    return max(50, b_avail), max(10, a_avail)


def build_delta_report(
    before_result: dict,
    after_result: dict,
    event: ChaosEvent,
) -> DeltaReport:
    """Build a before/after delta report from two simulation results."""
    b = _summarize(before_result)
    a = _summarize(after_result)

    b_avail, a_avail = _estimate_availability(b, a)

    # Determine root cause and mitigation
    root_cause = event.expected_effect
    mitigation = _suggest_mitigation(event, a)

    return DeltaReport(
        availability_before=round(b_avail, 2),
        availability_after=round(a_avail, 2),
        latency_p95_before=b["p95_ms"],
        latency_p95_after=a["p95_ms"],
        cost_before=b["cost_monthly"],
        cost_after=a["cost_monthly"],
        error_rate_before=0.0,
        error_rate_after=0.0,
        overloaded_nodes_before=b["overloaded_nodes"],
        overloaded_nodes_after=a["overloaded_nodes"],
        bottleneck_before=b["bottleneck"],
        bottleneck_after=a["bottleneck"],
        root_cause=root_cause,
        mitigation=mitigation,
    )


def _suggest_mitigation(event: ChaosEvent, after_summary: dict) -> str:
    """Suggest a mitigation based on the event type and outcome."""
    mitigations = {
        ChaosEventType.DB_FAILURE: "Add read replicas with automatic failover (e.g., Patroni for PostgreSQL, RDS Multi-AZ).",
        ChaosEventType.CACHE_FAILURE: "Deploy cache in clustered mode with replicas. Implement graceful degradation to DB.",
        ChaosEventType.QUEUE_FAILURE: "Use replicated queue clusters (Kafka 3+ brokers). Add dead-letter queues.",
        ChaosEventType.REGION_OUTAGE: "Deploy across multiple availability zones. Use global load balancer with failover.",
        ChaosEventType.NETWORK_LATENCY: "Add circuit breakers with timeout. Use connection pooling. Locate services in same AZ.",
        ChaosEventType.TRAFFIC_SPIKE: "Add auto-scaling groups. Implement rate limiting. Use CDN for static content.",
        ChaosEventType.HOT_KEY: "Use key sharding/consistent hashing. Add local in-process cache for hot keys.",
        ChaosEventType.CONSUMER_LAG: "Scale consumers horizontally. Partition queues. Add back-pressure mechanisms.",
        ChaosEventType.DEPENDENCY_OUTAGE: "Implement circuit breaker pattern. Add fallback responses. Use retry with exponential backoff.",
        ChaosEventType.HIT_RATIO_DROP: "Implement cache warming. Use TTL-based invalidation. Add write-through cache for hot data.",
    }
    return mitigations.get(event.id, "Review architecture for redundancy and fault tolerance.")


# ── Full chaos run ───────────────────────────────────────────────────────────

def run_chaos(
    graph: dict,
    event_id: ChaosEventType,
    traffic_rps: float | None = None,
    catalog: dict | None = None,
) -> ChaosRunResult:
    """
    Run a complete chaos scenario: before-simulation → inject → after-simulation → delta.

    Pure deterministic function.
    """
    from app.content.loader import load_catalog

    cat = catalog if catalog is not None else load_catalog()
    event = get_event(event_id)

    # Determine traffic RPS
    tm = graph.get("traffic_model") or {}
    rps = traffic_rps or tm.get("rps", 1000)

    # Before simulation
    before_input = SimulationInput(
        graph_json=graph,
        traffic=TrafficModel(total_rps=rps),
    )
    before_result = simulate(before_input, cat)
    before_dict = before_result.model_dump(mode="json")

    # Apply chaos
    chaos_graph = apply_chaos_event(graph, event, rps)

    # After simulation
    after_input = SimulationInput(
        graph_json=chaos_graph,
        traffic=TrafficModel(total_rps=rps),
    )
    after_result = simulate(after_input, cat)
    after_dict = after_result.model_dump(mode="json")

    # Build delta
    delta = build_delta_report(before_dict, after_dict, event)

    # Build outcomes
    affected_nodes = [
        n["id"] for n in chaos_graph.get("nodes", [])
        if n["type"] in event.affected_node_types or "*" in event.affected_node_types
    ]

    outcome = EventOutcome(
        event_id=event.id,
        event_name=event.name,
        affected_node_ids=affected_nodes,
        before_summary=_summarize(before_dict),
        after_summary=_summarize(after_dict),
        delta={
            "availability_drop": round(delta.availability_before - delta.availability_after, 2),
            "latency_increase_ms": round(delta.latency_p95_after - delta.latency_p95_before, 2),
        },
        severity=_classify_severity(delta),
    )

    return ChaosRunResult(
        event_id=event.id,
        event_name=event.name,
        before_simulation=before_dict,
        after_simulation=after_dict,
        delta_report=delta,
        outcomes=[outcome],
    )


def _classify_severity(delta: DeltaReport) -> str:
    """Classify the severity of a chaos event outcome."""
    avail_drop = delta.availability_before - delta.availability_after
    latency_increase = delta.latency_p95_after - delta.latency_p95_before

    if avail_drop > 30 or delta.availability_after < 50:
        return "critical"
    if avail_drop > 15 or latency_increase > 500:
        return "high"
    if avail_drop > 5 or latency_increase > 100:
        return "medium"
    return "low"
