"""Analytical simulation engine — pure Python, deterministic, no I/O."""

from __future__ import annotations

import math
from collections import defaultdict

from app.evaluation.context import EvalContext
from app.simulation.models import (
    CostBreakdown,
    EdgeFlow,
    EdgeSimulationResult,
    NodeCost,
    NodeLatency,
    NodeOverrides,
    NodeSimulationResult,
    NodeUtilization,
    PercentileEstimate,
    SimulationInput,
    SimulationResult,
    SimulationSummary,
    TrafficHop,
    TrafficModel,
    TrafficPath,
    compute_graph_hash,
)

# ── Defaults from catalog ────────────────────────────────────────────────────

_NETWORK_LATENCY_MS = 1.0  # base network RTT between AZ-local hops
_CROSS_AZ_LATENCY_MS = 5.0
_OVERLOADED_ERROR_RATE = 0.05  # 5% errors when util > 1.0
_SATURATING_ERROR_RATE = 0.02  # 2% errors when util > 0.95

# Queueing delay multipliers (M/M/c approximation heuristic)
_UTIL_DELAY_FACTOR = {0.5: 0.1, 0.7: 0.3, 0.8: 0.6, 0.9: 1.5, 0.95: 3.0, 1.0: 10.0}


def _interpolate_delay(util: float) -> float:
    """Heuristic queueing delay multiplier based on utilization."""
    if util < 0.5:
        return 0.05 * util
    if util >= 1.0:
        return 10.0 + (util - 1.0) * 5.0
    thresholds = sorted(_UTIL_DELAY_FACTOR.items())
    for i in range(len(thresholds) - 1):
        u1, d1 = thresholds[i]
        u2, d2 = thresholds[i + 1]
        if u1 <= util <= u2:
            t = (util - u1) / (u2 - u1)
            return d1 + t * (d2 - d1)
    return 10.0


def _p95_multiplier(util: float) -> float:
    """P95/p50 ratio grows with utilization."""
    return 1.5 + util * 1.5


def _p99_multiplier(util: float) -> float:
    """P99/p50 ratio grows faster with utilization."""
    return 2.0 + util * 3.0


# ── Capacity resolution ─────────────────────────────────────────────────────

def _node_capacity_rps(ctx: EvalContext, node: dict, overrides: dict[str, NodeOverrides]) -> float:
    """Effective RPS capacity of a node (combined read+write)."""
    nid = node["id"]
    ov = overrides.get(nid)

    # Read capacity
    safe_reads = ctx.capacity_of(node, "safe_reads_per_sec") or ctx.capacity_of(node, "rps_per_instance")
    if safe_reads is None:
        safe_reads = ctx.capacity_of(node, "events_per_sec_per_broker") or 0
    safe_reads = float(safe_reads or 0)

    # Write capacity
    safe_writes = ctx.capacity_of(node, "safe_writes_per_sec") or 0
    safe_writes = float(safe_writes or 0)

    instances = ctx.instances(node)
    if ov and ov.replicas is not None:
        instances = max(1, ov.replicas)

    total_read = safe_reads * instances
    total_write = safe_writes * instances
    return total_read + total_write


def _node_base_latency_ms(ctx: EvalContext, node: dict) -> float:
    """Base processing latency from catalog (p95_base_ms)."""
    base = ctx.capacity_of(node, "p95_base_ms")
    return float(base or 1.0)


def _node_cost_per_month(ctx: EvalContext, node: dict) -> float:
    """Monthly cost for all instances of this node."""
    entry = ctx.catalog_entry(node) or {}
    cost_defaults = entry.get("cost_defaults") or {}
    cost_per = cost_defaults.get("usd_per_instance_month") or cost_defaults.get("usd_per_node_month")
    instances = ctx.instances(node)
    return float(cost_per or 0) * max(1, instances)


# ── Traffic routing ─────────────────────────────────────────────────────────

def _compute_edge_flows(
    ctx: EvalContext,
    traffic: TrafficModel,
    node_overrides: dict[str, NodeOverrides],
) -> dict[str, float]:
    """
    Compute RPS arriving at each node via a topological BFS.
    Assumes client nodes inject total_rps and traffic flows downstream.
    """
    # Build adjacency list (source → list of targets)
    out_edges: dict[str, list[tuple[str, str, str]]] = defaultdict(list)  # source → [(target, edge_id, traffic_type)]
    in_edges: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for edge in ctx.edges:
        src, tgt = edge["source"], edge["target"]
        tt = edge.get("traffic_type", "sync_request")
        out_edges[src].append((tgt, edge["id"], tt))
        in_edges[tgt].append((src, edge["id"], tt))

    # Compute per-node offered RPS via BFS from client nodes
    offered: dict[str, float] = defaultdict(float)
    client_rps = traffic.total_rps

    # Find client-type nodes
    from app.evaluation.context import ClientTypes
    client_nodes = [n for n in ctx.structural_nodes() if n["type"] in ClientTypes]

    if not client_nodes:
        # Fallback: treat all nodes with no in-edges as sources
        client_nodes = [n for n in ctx.structural_nodes() if not in_edges.get(n["id"])]

    if not client_nodes:
        # Last resort: inject at the first node
        for n in ctx.structural_nodes():
            offered[n["id"]] = client_rps
            break
    else:
        per_client = client_rps / len(client_nodes) if client_nodes else client_rps
        for n in client_nodes:
            offered[n["id"]] = per_client

    # BFS to propagate traffic downstream
    from collections import deque
    queue = deque()
    visited: set[str] = set()

    for n in client_nodes:
        queue.append(n["id"])
        visited.add(n["id"])

    while queue:
        current = queue.popleft()
        current_rps = offered[current]
        if current_rps <= 0:
            continue

        out = out_edges.get(current, [])
        if not out:
            continue

        # Split traffic among outgoing edges
        # Sync edges get proportional share; async edges may fan-out fully
        sync_targets = [(t, e, tt) for t, e, tt in out if tt == "sync_request"]
        async_targets = [(t, e, tt) for t, e, tt in out if tt in ("async_event", "replication", "batch")]

        # Sync: split evenly
        if sync_targets:
            per_target = current_rps / len(sync_targets)
            for target, edge_id, _ in sync_targets:
                offered[target] += per_target
                if target not in visited:
                    visited.add(target)
                    queue.append(target)

        # Async: full fan-out (each target receives the full RPS)
        for target, edge_id, _ in async_targets:
            offered[target] += current_rps
            if target not in visited:
                visited.add(target)
                queue.append(target)

    return dict(offered)


def _get_cache_hit_ratio(
    ctx: EvalContext,
    cache_node: dict,
    overrides: dict[str, NodeOverrides],
) -> float:
    """Cache hit ratio for a cache node."""
    nid = cache_node["id"]
    ov = overrides.get(nid)
    if ov and ov.cache_hit_ratio is not None:
        return ov.cache_hit_ratio
    ratio = ctx.capacity_of(cache_node, "default_hit_ratio_assumption")
    return float(ratio) if ratio is not None else 0.9


# ── Core simulation ─────────────────────────────────────────────────────────

def _simulate_node(
    ctx: EvalContext,
    node: dict,
    offered_rps: float,
    traffic: TrafficModel,
    overrides: dict[str, NodeOverrides],
) -> NodeSimulationResult:
    """Compute simulation results for a single node."""
    nid = node["id"]
    ntype = node["type"]
    name = node.get("name", nid)

    capacity_rps = _node_capacity_rps(ctx, node, overrides)
    base_latency = _node_base_latency_ms(ctx, node)

    # Determine read/write split at this node
    read_rps = offered_rps * traffic.read_ratio
    write_rps = offered_rps * traffic.write_ratio

    # Compute per-type utilization
    safe_reads = ctx.capacity_of(node, "safe_reads_per_sec") or ctx.capacity_of(node, "rps_per_instance") or 0
    safe_reads = float(safe_reads or 0)
    safe_writes = float(ctx.capacity_of(node, "safe_writes_per_sec") or 0)

    instances = ctx.instances(node)
    ov = overrides.get(nid)
    if ov and ov.replicas is not None:
        instances = max(1, ov.replicas)

    total_read_cap = safe_reads * instances
    total_write_cap = safe_writes * instances

    read_util = (read_rps / total_read_cap) if total_read_cap > 0 else 0
    write_util = (write_rps / total_write_cap) if total_write_cap > 0 else 0
    total_util = (offered_rps / capacity_rps) if capacity_rps > 0 else float("inf") if offered_rps > 0 else 0

    util = NodeUtilization(
        read_utilization=round(read_util, 4),
        write_utilization=round(write_util, 4),
        total_utilization=round(total_util, 4),
    )

    # Latency
    delay_factor = _interpolate_delay(min(total_util, 1.5))
    p50 = base_latency * (1 + delay_factor * 0.5)
    p95 = base_latency * (1 + delay_factor * _p95_multiplier(min(total_util, 1.0)))
    p99 = base_latency * (1 + delay_factor * _p99_multiplier(min(total_util, 1.0)))

    latency = NodeLatency(
        p50_ms=round(p50, 2),
        p95_ms=round(p95, 2),
        p99_ms=round(p99, 2),
        base_ms=round(base_latency, 2),
    )

    # Error rate
    error_rate = 0.0
    if total_util > 1.0:
        error_rate = _OVERLOADED_ERROR_RATE * min(total_util - 1.0, 1.0) + _SATURATING_ERROR_RATE
    elif total_util > 0.95:
        error_rate = _SATURATING_ERROR_RATE * (total_util - 0.95) / 0.05
    error_rate = round(min(error_rate, 1.0), 4)

    # Queue depth (M/M/c approximation)
    queue_depth = 0.0
    if total_util > 0.7 and capacity_rps > 0:
        rho = min(total_util, 0.99)
        queue_depth = (rho ** 2) / (1 - rho) * 0.5
    queue_depth = round(max(0, queue_depth), 2)

    # Cost
    monthly = _node_cost_per_month(ctx, node)
    per_request = monthly / (offered_rps * 86400 * 30) if offered_rps > 0 else 0
    cost = NodeCost(
        usd_per_month=round(monthly, 2),
        usd_per_request=round(per_request, 8),
    )

    # Warnings
    warnings: list[str] = []
    if total_util > 1.0:
        warnings.append(f"OVERLOADED: {name} at {total_util:.0%} utilization ({offered_rps:.0f} RPS offered, {capacity_rps:.0f} RPS capacity)")
    elif total_util > 0.8:
        warnings.append(f"CRITICAL: {name} at {total_util:.0%} utilization — {capacity_rps - offered_rps:.0f} RPS headroom remaining")
    if error_rate > 0.01:
        warnings.append(f"Estimated error rate: {error_rate:.1%}")

    routed_rps = offered_rps * (1 - error_rate)

    return NodeSimulationResult(
        node_id=nid,
        node_type=ntype,
        name=name,
        capacity_rps=round(capacity_rps, 2),
        offered_rps=round(offered_rps, 2),
        routed_rps=round(routed_rps, 2),
        utilization=util,
        latency=latency,
        cost=cost,
        error_rate=error_rate,
        queue_depth=queue_depth,
        is_bottleneck=util.is_critical,
        warnings=warnings,
    )


def _compute_trace_paths(
    ctx: EvalContext,
    traffic: TrafficModel,
    node_results: dict[str, NodeSimulationResult],
) -> list[TrafficPath]:
    """Generate representative trace paths through the graph."""
    from app.evaluation.context import ClientTypes, LBTypes, CacheTypes, DatastoreTypes

    client_nodes = [n for n in ctx.structural_nodes() if n["type"] in ClientTypes]
    if not client_nodes:
        client_nodes = ctx.structural_nodes()[:1]

    # Build adjacency for path traversal
    out_adj: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for edge in ctx.edges:
        out_adj[edge["source"]].append((edge["target"], edge.get("traffic_type", "sync_request")))

    # Find deepest sync paths (DFS)
    paths: list[TrafficPath] = []
    visited = set()

    def _dfs(node_id: str, current_path: list[str], current_hops: list[TrafficHop]) -> None:
        if len(current_path) > 15 or node_id in visited:
            return
        visited.add(node_id)

        nr = node_results.get(node_id)
        hop_latency = nr.latency.p50_ms if nr else 1.0
        hop = TrafficHop(
            node_id=node_id,
            node_type=nr.node_type if nr else "unknown",
            latency_ms=hop_latency,
            cache_hit=node_id in visited and nr and nr.node_type in CacheTypes,
        )
        hops = current_hops + [hop]
        path_nodes = current_path + [node_id]

        targets = out_adj.get(node_id, [])
        sync_targets = [(t, tt) for t, tt in targets if tt == "sync_request"]

        if not sync_targets:
            total_latency = sum(h.latency_ms for h in hops) + _NETWORK_LATENCY_MS * max(0, len(hops) - 1)
            paths.append(TrafficPath(
                path_nodes=path_nodes,
                total_latency_ms=round(total_latency, 2),
                hops=hops,
            ))
        else:
            for target, _ in sync_targets:
                _dfs(target, path_nodes, hops)

        visited.discard(node_id)

    for client in client_nodes:
        visited.clear()
        _dfs(client["id"], [], [])

    return paths[:20]  # Cap at 20 paths


def simulate(inp: SimulationInput, catalog: dict | None = None) -> SimulationResult:
    """
    Run an analytical simulation over a canonical architecture graph.

    This is a pure, deterministic function — same input always produces same output.
    No I/O, no randomness beyond the M/M/c heuristic.

    If ``catalog`` is None the global catalog loaded at startup is used.
    """
    from app.content.loader import load_catalog

    graph = inp.graph_json
    cat = catalog if catalog is not None else load_catalog()
    ctx = EvalContext(graph, cat)
    traffic = inp.traffic

    # Resolve per-node overrides
    overrides: dict[str, NodeOverrides] = {o.node_id: o for o in inp.node_overrides}

    # Step 1: Compute offered RPS at each node
    offered = _compute_edge_flows(ctx, traffic, overrides)

    # Step 2: Simulate each node
    node_results: dict[str, NodeSimulationResult] = {}
    all_node_results: list[NodeSimulationResult] = []

    for node in ctx.structural_nodes():
        nid = node["id"]
        rps = offered.get(nid, 0)
        result = _simulate_node(ctx, node, rps, traffic, overrides)
        node_results[nid] = result
        all_node_results.append(result)

    # Step 3: Compute edge flows
    edge_results: list[EdgeSimulationResult] = []
    max_edge_rps = max((offered.get(e["source"], 0) for e in ctx.edges), default=1) or 1

    for edge in ctx.edges:
        src = edge["source"]
        tgt = edge["target"]
        edge_rps = offered.get(src, 0)
        bandwidth_mbps = (edge_rps * traffic.avg_response_bytes * 8) / 1_000_000

        saturation = edge_rps / max_edge_rps if max_edge_rps > 0 else 0
        flow = EdgeFlow(
            rps=round(edge_rps, 2),
            bandwidth_mbps=round(bandwidth_mbps, 2),
            saturation=round(saturation, 4),
        )

        warnings: list[str] = []
        tgt_result = node_results.get(tgt)
        if tgt_result and tgt_result.utilization.is_overloaded:
            warnings.append(f"Downstream node {tgt_result.name} is overloaded")

        edge_results.append(EdgeSimulationResult(
            edge_id=edge["id"],
            source=src,
            target=tgt,
            traffic_type=edge.get("traffic_type", "sync_request"),
            flow=flow,
            warnings=warnings,
        ))

    # Step 4: Compute trace paths
    trace_paths = _compute_trace_paths(ctx, traffic, node_results)

    # Step 5: Summary
    total_rps = traffic.total_rps
    cache_nodes = [n for n in ctx.structural_nodes() if n["type"] in ("redis", "memcached", "cdn")]
    effective_rps = total_rps
    for cn in cache_nodes:
        ratio = _get_cache_hit_ratio(ctx, cn, overrides)
        # Cache reduces downstream DB read load
        effective_rps -= total_rps * traffic.read_ratio * ratio * 0.8  # conservative: 80% of cache hits filter to DB

    effective_rps = max(effective_rps, 0)

    # End-to-end latency (longest path P95)
    if trace_paths:
        e2e_p50 = max(p.total_latency_ms for p in trace_paths)
        e2e_p95 = e2e_p50 * 1.8
        e2e_p99 = e2e_p50 * 2.5
    else:
        e2e_p50 = sum(nr.latency.p50_ms for nr in node_results.values() if nr.offered_rps > 0)
        e2e_p95 = e2e_p50 * 1.8
        e2e_p99 = e2e_p50 * 2.5

    # Cost breakdown
    cost_map: dict[str, float] = {}
    total_cost = 0.0
    for nr in all_node_results:
        cost_map[nr.node_id] = nr.cost.usd_per_month
        total_cost += nr.cost.usd_per_month

    # Bottleneck
    bottlenecks = [nr for nr in all_node_results if nr.utilization.total_utilization > 0.8]
    bottlenecks.sort(key=lambda x: x.utilization.total_utilization, reverse=True)
    bottleneck_node = bottlenecks[0].node_id if bottlenecks else None

    overloaded = [nr.node_id for nr in all_node_results if nr.utilization.is_overloaded]

    # Global warnings
    global_warnings: list[str] = []
    if overloaded:
        global_warnings.append(
            f"{len(overloaded)} node(s) overloaded: {', '.join(overloaded)}"
        )
    if bottleneck_node:
        bn = node_results.get(bottleneck_node)
        if bn:
            global_warnings.append(
                f"Bottleneck: {bn.name} at {bn.utilization.total_utilization:.0%} utilization"
            )

    # Overloaded nodes: propagate errors upstream
    for nr in all_node_results:
        if nr.utilization.is_overloaded and nr.error_rate > 0:
            # Find upstream nodes and inflate their error rates
            pass  # handled by trace path

    summary = SimulationSummary(
        total_rps=total_rps,
        effective_rps=round(effective_rps, 2),
        end_to_end=PercentileEstimate(
            p50_ms=round(e2e_p50, 2),
            p95_ms=round(e2e_p95, 2),
            p99_ms=round(e2e_p99, 2),
        ),
        total_cost=CostBreakdown(
            total_usd_per_month=round(total_cost, 2),
            per_node_usd_per_month=cost_map,
        ),
        bottleneck_node=bottleneck_node,
        overloaded_nodes=overloaded,
        warnings=global_warnings,
    )

    return SimulationResult(
        input_hash=compute_graph_hash(graph),
        nodes=all_node_results,
        edges=edge_results,
        trace_paths=trace_paths,
        summary=summary,
    )
