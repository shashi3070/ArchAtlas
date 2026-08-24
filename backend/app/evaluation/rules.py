"""Deterministic evaluation rules.

Every function is pure and returns zero or more RuleResult-shaped dicts.
Property conventions consumed here (set via canvas inspector or content):

- node.properties.auth / authorization_checks / metrics / logs / tracing /
  alerts / secrets_managed   (booleans)
- node.properties.idempotent_consumer (bool)
- node.availability.replicas / multi_az / multi_region / failover
- node.deployment.region
- edge.properties.retry (bool), timeout_ms (int), backoff ("exponential")

Missing configuration means the platform reports UNKNOWN/low confidence
rather than inventing an answer.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from app.evaluation.context import (
    CacheTypes,
    ComputeTypes,
    DatastoreTypes,
    EvalContext,
    QueueTypes,
    json_str,
)

json_text = json_str  # readable alias used throughout the rules

Status = str  # PASS | WARNING | FAIL | INFO | UNKNOWN


def result(
    rule_id: str,
    status: Status,
    message: str,
    *,
    severity: str = "medium",
    evidence: list[str] | None = None,
    affected_nodes: list[str] | None = None,
    affected_edges: list[str] | None = None,
    requirement_ids: list[str] | None = None,
    confidence: str = "high",
    confidence_reason: str | None = None,
    suggested_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "status": status,
        "message": message,
        "severity": severity,
        "evidence": evidence or [],
        "affected_nodes": affected_nodes or [],
        "affected_edges": affected_edges or [],
        "requirement_ids": requirement_ids or [],
        "confidence": confidence,
        "confidence_reason": confidence_reason if confidence != "high" else None,
        "suggested_actions": suggested_actions or [],
    }


def unknown(rule_id: str, reason: str) -> dict[str, Any]:
    return result(
        rule_id,
        "UNKNOWN",
        f"Cannot evaluate: {reason}",
        confidence="low",
        confidence_reason=reason,
    )


# ---------------------------------------------------------------- graph


def r_graph_disconnected_required(ctx: EvalContext) -> list[dict[str, Any]]:
    if not ctx.required_components:
        return []
    out = []
    reachable = ctx.reachable_from_clients()
    for ctype in ctx.required_components:
        nodes = [n for n in ctx.nodes_of_type(ctype)]
        for n in nodes:
            if n["id"] not in reachable:
                out.append(
                    result(
                        "graph.disconnected_required_component",
                        "FAIL",
                        f"Required component '{n.get('name')}' ({ctype}) is unreachable from any"
                        f"client.",
                        severity="high",
                        affected_nodes=[n["id"]],
                        suggested_actions=[
                            {"action": f"Connect {n['id']} into the request path"}
                        ],
                    )
                )
    return out


def r_graph_invalid_edge(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for e in ctx.edges:
        if e.get("source") == e.get("target"):
            out.append(
                result(
                    "graph.invalid_edge",
                    "FAIL",
                    f"Edge '{e.get('id')}' connects node '{e.get('source')}' to itself.",
                    severity="high",
                    affected_edges=[str(e.get("id"))],
                )
            )
    return out


def _missing_endpoint(ctx: EvalContext, side: str) -> list[dict[str, Any]]:
    out = []
    for e in ctx.edges:
        ref = e.get(side)
        if ref not in ctx.nodes_by_id:
            out.append(
                result(
                    f"graph.missing_{side}",
                    "FAIL",
                    f"Edge '{e.get('id')}' references missing {side} node '{ref}'.",
                    severity="medium",
                    affected_edges=[str(e.get("id"))],
                )
            )
    return out


def r_graph_missing_source(ctx: EvalContext) -> list[dict[str, Any]]:
    return _missing_endpoint(ctx, "source")


def r_graph_missing_destination(ctx: EvalContext) -> list[dict[str, Any]]:
    return _missing_endpoint(ctx, "target")


def r_graph_inappropriate_cycle(ctx: EvalContext) -> list[dict[str, Any]]:
    cycles = ctx.sync_cycle_exists()
    out = []
    for cycle in cycles:
        out.append(
            result(
                "graph.inappropriate_cycle",
                "WARNING",
                "Synchronous request path forms a cycle: "
                + " -> ".join(cycle),
                affected_nodes=cycle,
                confidence="medium",
                confidence_reason=(
                    "cycle detection follows sync edges; "
                    "intentional bidirectional pairs may be fine"
                ),
            )
        )
    return out


def r_graph_no_ingress(ctx: EvalContext) -> list[dict[str, Any]]:
    if not ctx.nodes:
        return []
    clients = ctx.client_nodes()
    if not clients:
        return [
            result(
                "graph.no_ingress",
                "FAIL",
                "Architecture has no client component - there is no entry point.",
                severity="critical",
                suggested_actions=[{"action": "Add a client component as ingress"}],
            )
        ]
    reachable = ctx.reachable_from_clients()
    non_client = [n for n in ctx.structural_nodes() if n.get("type") != "client"]
    if non_client and not (reachable & {n["id"] for n in non_client}):
        return [
            result(
                "graph.no_ingress",
                "FAIL",
                "No component is reachable from any client - requests go nowhere.",
                severity="critical",
                suggested_actions=[
                    {"action": "Draw connections from the client toward backend components"}
                ],
            )
        ]
    return []


def r_graph_no_data_store(ctx: EvalContext) -> list[dict[str, Any]]:
    """Persistence need comes from REQUIREMENTS (text or required_components).

    Inferring 'you must store data' purely from a nonzero write ratio proved
    too noisy - every async pipeline would trip it. Evidence over vibes.
    """
    persistence_words = ("store", "persist", "save", "database")
    needs_persistence = False
    why: list[str] = []
    for req in ctx.requirements:
        rules_text = json_text(req.get("validation_rules") or "") or ""
        blob = (str(req.get("description", "")) + " " + rules_text).lower()
        hit = [w for w in persistence_words if w in blob]
        if hit:
            needs_persistence = True
            why.append(f"requirement '{req.get('id')}' mentions {hit[0]}")
    wanted_types = {t for t in ctx.required_components if t in DatastoreTypes}
    if wanted_types:
        needs_persistence = True
        why.append(f"challenge requires component(s): {sorted(wanted_types)}")
    if not needs_persistence:
        return []
    if ctx.has_type(*DatastoreTypes):
        return [
            result(
                "graph.no_data_store_required",
                "PASS",
                "Persistence requirement satisfied by present datastore(s).",
                evidence=[f"inferred need: {'; '.join(why)}"],
            )
        ]
    return [
        result(
            "graph.no_data_store_required",
            "FAIL",
            "Requirements imply persistence but no database/storage component exists.",
            severity="critical",
            evidence=[f"persistence inferred from: {'; '.join(why)}"],
            suggested_actions=[
                {
                    "action": "Add postgresql (relational default) "
                    "or mongodb/object_storage as fits the workload"
                }
            ],
        )
    ]


# ---------------------------------------------------------------- scale


def r_scale_single_compute_high_traffic(ctx: EvalContext) -> list[dict[str, Any]]:
    demand, why = _demand_or_unknown(ctx)
    if demand is None:
        return [unknown("scale.single_compute_high_traffic", why)]
    apis = ctx.nodes_of_type("api")
    if not apis:
        return []
    per_instance = None
    for api in apis:
        cap = ctx.capacity_of(api, "rps_per_instance")
        if cap:
            per_instance = cap
            break
    if per_instance is None:
        defaults = (ctx.catalog.get("api") or {}).get("capacity_defaults", {})
        per_instance = float(defaults.get("rps_per_instance", 1000))
    total_cap = per_instance * ctx.total_instances("api")
    if total_cap < demand:
        return [
            result(
                "scale.single_compute_high_traffic",
                "FAIL",
                f"API tier capacity {total_cap:.0f} rps < demand {demand:.0f} rps.",
                severity="critical",
                evidence=[
                    f"demand: {demand:.0f} rps ({why})",
                    f"capacity: {ctx.total_instances('api')} instance(s) x {per_instance:.0f} rps",
                ],
                affected_nodes=[a["id"] for a in apis],
                suggested_actions=[
                    {
                        "action": "Increase API replicas to at least "
                        f"{int(-(-demand // per_instance))} instances",
                        "tradeoffs": ["more instances = higher cost"],
                    }
                ],
            )
        ]
    return [
        result(
            "scale.single_compute_high_traffic",
            "PASS",
            f"API tier capacity {total_cap:.0f} rps covers demand {demand:.0f} rps.",
            evidence=[f"{ctx.total_instances('api')} api instances"],
        )
    ]


def r_scale_db_write_bottleneck(ctx: EvalContext) -> list[dict[str, Any]]:
    write_rps, why = ctx.write_rps()
    if write_rps is None:
        return []
    stores = ctx.nodes_of_type("postgresql", "mongodb")
    if not stores:
        return []
    out = []
    queues_present = ctx.has_type(*QueueTypes)
    for store in stores:
        cap = ctx.capacity_of(store, "safe_writes_per_sec") or 5000.0
        # Sharding multiplies write capacity by shard count when declared.
        shards = store.get("availability", {}).get("shards")
        multiplier = float(shards) if isinstance(shards, int) and shards > 1 else 1.0
        effective = cap * multiplier * max(1, ctx.instances(store))
        if write_rps > effective:
            buffered = ", writes are queued/buffered" if queues_present else ""
            out.append(
                result(
                    "scale.db_write_bottleneck",
                    "FAIL",
                    f"Write demand {write_rps:.0f}/s exceeds safe write capacity {effective:.0f}/s"
                    f"of {store.get('name')}.{buffered}",
                    severity="critical",
                    evidence=[
                        f"write demand: {write_rps:.0f}/s ({why})",
                        f"safe_writes_per_sec: {cap:.0f} x {multiplier:g} shard(s)",
                    ],
                    affected_nodes=[store["id"]],
                    suggested_actions=[
                        {"action": "Buffer writes through a queue and batch them"},
                        {
                            "action": "Shard the datastore by a high-cardinality key",
                            "tradeoffs": [
                                "cross-shard queries become scatter-gather"
                            ],
                        },
                    ],
                )
            )
    return out


def r_scale_db_read_bottleneck(ctx: EvalContext) -> list[dict[str, Any]]:
    read_rps_value, why = ctx.read_rps()
    if read_rps_value is None:
        return []
    stores = ctx.nodes_of_type("postgresql", "mongodb")
    if not stores:
        return []
    cache_inline = ctx.cache_is_inline() and ctx.has_type(*CacheTypes)
    hit_ratio = 0.9 if cache_inline else 0.0
    out = []
    for store in stores:
        cap = ctx.capacity_of(store, "safe_reads_per_sec") or 15000.0
        replicas = ctx.instances(store)
        effective = cap * replicas
        served_from_store = read_rps_value * (1 - hit_ratio)
        if served_from_store > effective:
            advice = (
                "Place redis between compute and the datastore (cache-aside)"
                if not cache_inline
                else "Add read replicas to the datastore"
            )
            out.append(
                result(
                    "scale.db_read_bottleneck",
                    "FAIL",
                    f"Read demand {served_from_store:.0f}/s reaches {store.get('name')} but"
                    f"capacity is {effective:.0f}/s.",
                    severity="critical",
                    evidence=[
                        f"read demand: {read_rps_value:.0f}/s ({why})",
                        f"cache absorption: {hit_ratio:.0%}"
                        + ("" if cache_inline else " (cache missing/off-path)"),
                        f"store capacity: {cap:.0f}/s x {replicas} instance(s)",
                    ],
                    affected_nodes=[store["id"]],
                    suggested_actions=[{"action": advice}],
                )
            )
    return out


def _demand_or_unknown(ctx: EvalContext) -> tuple[float | None, str]:
    value = ctx.demand_rps()
    if value is None:
        return None, "no traffic_model.rps and no rps validation rule declared"
    return value, "declared traffic model"


def r_scale_insufficient_worker_capacity(ctx: EvalContext) -> list[dict[str, Any]]:
    workers = ctx.nodes_of_type("worker")
    if not workers:
        return []
    arrival = _queue_arrival_estimate(ctx)
    if arrival is None:
        return []
    per_worker = None
    for w in workers:
        cap = ctx.capacity_of(w, "jobs_per_sec_per_instance")
        if cap:
            per_worker = cap
            break
    if per_worker is None:
        return []
    capacity = per_worker * sum(ctx.instances(w) for w in workers)
    if arrival > capacity:
        return [
            result(
                "scale.insufficient_worker_capacity",
                "FAIL",
                f"Worker pool processes {capacity:.0f} jobs/s but ~{arrival:.0f}/s arrive.",
                severity="high",
                evidence=[
                    f"arrival estimate: {arrival:.0f}/s (async inflow to queues)",
                    f"capacity: {sum(ctx.instances(w) for w in workers)} worker(s) x"
                    f"{per_worker:.0f}/s",
                ],
                affected_nodes=[w["id"] for w in workers],
                suggested_actions=[{"action": "Scale worker replicas with backlog depth"}],
            )
        ]
    return [
        result(
            "scale.insufficient_worker_capacity",
            "PASS",
            f"Worker capacity {capacity:.0f}/s covers estimated arrival {arrival:.0f}/s.",
        )
    ]


def _queue_arrival_estimate(ctx: EvalContext) -> float | None:
    """Async inflow into queues = share of demand routed async (heuristic)."""
    demand = ctx.demand_rps()
    if demand is None:
        return None
    inflow = 0.0
    has_async = False
    for src, dst in ctx.edges_between(ComputeTypes | {"client"}, QueueTypes):
        del src, dst
        has_async = True
        break
    if has_async:
        write_share = 1 - (ctx.read_ratio if ctx.read_ratio is not None else 0.8)
        inflow = demand * write_share
    return inflow if has_async else None


def r_scale_queue_consumer_shortage(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for queue in ctx.nodes_of_type(*QueueTypes):
        consumers = ctx.queue_consumers(queue)
        if not consumers:
            out.append(
                result(
                    "scale.queue_consumer_shortage",
                    "FAIL",
                    f"'{queue.get('name')}' receives events but nothing consumes them.",
                    severity="high",
                    affected_nodes=[queue["id"]],
                    suggested_actions=[{"action": "Connect worker(s) to consume from the queue"}],
                )
            )
    return out


def r_scale_partition_hot_spot(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for node in ctx.nodes_of_type(*QueueTypes | DatastoreTypes):
        props = node.get("properties") or {}
        partitions = props.get("partitions") or props.get("shards")
        if partitions == 1:
            out.append(
                result(
                    "scale.partition_hot_spot",
                    "WARNING",
                    f"'{node.get('name')}' declares a single partition/shard - one key range takes"
                    f"all load.",
                    severity="medium",
                    affected_nodes=[node["id"]],
                    suggested_actions=[
                        {"action": "Use >=3 partitions with a high-cardinality key"}
                    ],
                )
            )
    return out


def r_scale_missing_load_balancing(ctx: EvalContext) -> list[dict[str, Any]]:
    if not ctx.has_type("load_balancer"):
        apis_multi = [a for a in ctx.nodes_of_type("api") if ctx.instances(a) > 1]
        all_api_ids = [a["id"] for a in ctx.nodes_of_type("api")]
        if len(all_api_ids) > 1 or apis_multi:
            return [
                result(
                    "scale.missing_load_balancing",
                    "WARNING",
                    "Multiple API instances exist but no load balancer distributes traffic.",
                    severity="high",
                    affected_nodes=[a["id"] for a in apis_multi] or all_api_ids,
                    suggested_actions=[{"action": "Add a load balancer in front of the API tier"}],
                )
            ]
    return []


def r_scale_missing_horizontal_scaling(ctx: EvalContext) -> list[dict[str, Any]]:
    demand, _why = _demand_or_unknown(ctx)
    single_apis = [a for a in ctx.nodes_of_type("api") if ctx.instances(a) == 1]
    if single_apis and demand is not None and demand > 1000:
        return [
            result(
                "scale.missing_horizontal_scaling",
                "FAIL",
                f"API runs a single instance against {demand:.0f} rps demand.",
                severity="high",
                affected_nodes=[a["id"] for a in single_apis],
                suggested_actions=[{"action": "Set replicas >= 2 and distribute across AZs"}],
            )
        ]
    return []


# ---------------------------------------------------------------- availability


def r_ha_single_database(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for store in ctx.nodes_of_type("postgresql", "mongodb"):
        avail = store.get("availability") or {}
        replicas = int(avail.get("replicas") or 0)
        if ctx.instances(store) < 2:
            out.append(
                result(
                    "ha.single_database",
                    "FAIL",
                    f"'{store.get('name')}' is a lone instance - its failure loses all data"
                    f"access.",
                    severity="critical",
                    affected_nodes=[store["id"]],
                    suggested_actions=[
                        {"action": "Add at least one standby replica with automatic failover"}
                    ],
                )
            )
        elif replicas == 0:
            out.append(
                result(
                    "ha.single_database",
                    "INFO",
                    f"'{store.get('name')}' scales horizontally via catalog defaults; declare"
                    f"explicit replicas for clarity.",
                    severity="low",
                    affected_nodes=[store["id"]],
                )
            )
    return out


def r_ha_single_cache(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    inline = ctx.cache_is_inline()
    for cache in ctx.nodes_of_type(*CacheTypes):
        if ctx.instances(cache) < 2 and inline:
            out.append(
                result(
                    "ha.single_cache",
                    "WARNING",
                    f"'{cache.get('name')}' sits on the critical read path with a single node;"
                    f"failure shifts full load to the DB.",
                    severity="high",
                    affected_nodes=[cache["id"]],
                    suggested_actions=[
                        {"action": "Run redis as a replicated group with automatic failover"}
                    ],
                )
            )
    return out


def r_ha_single_compute_node(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for api in ctx.nodes_of_type("api"):
        if ctx.instances(api) < 2:
            out.append(
                result(
                    "ha.single_compute_node",
                    "WARNING",
                    f"'{api.get('name')}' runs one instance; deployment restarts cause"
                    f"user-visible errors.",
                    severity="high",
                    affected_nodes=[api["id"]],
                )
            )
    return out


def r_ha_single_region(ctx: EvalContext) -> list[dict[str, Any]]:
    target = ctx.availability_target()
    if target is None or target < 99.9:
        return []
    regions = {
        str((n.get("deployment") or {}).get("region") or "default")
        for n in ctx.nodes
        if n.get("type") != "client"
    }
    multi_region_declared = any(
        bool((n.get("availability") or {}).get("multi_region"))
        for n in ctx.nodes
        if n.get("type") != "client"
    )
    if len(regions) <= 1 and not multi_region_declared:
        return [
            result(
                "ha.single_region",
                "WARNING",
                f"Availability target {target}% usually requires surviving a region outage;"
                f"everything deploys to region(s): {sorted(regions)}.",
                severity="medium",
                confidence="medium",
                confidence_reason="region outage math depends on provider SLA assumptions",
            )
        ]
    return []


def r_ha_single_load_balancer(ctx: EvalContext) -> list[dict[str, Any]]:
    lbs = ctx.nodes_of_type("load_balancer")
    if not lbs:
        return []
    out = []
    for lb in lbs:
        if ctx.instances(lb) < 2:
            out.append(
                result(
                    "ha.single_load_balancer",
                    "WARNING",
                    f"'{lb.get('name')}' is a single instance - it fronts everything and can fail"
                    f"alone.",
                    severity="high",
                    affected_nodes=[lb["id"]],
                    suggested_actions=[
                        {"action": "Use an active/passive pair or managed anycast LB"}
                    ],
                )
            )
    return out


def r_ha_missing_failover(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for node in ctx.nodes:
        if node.get("type") == "client":
            continue
        avail = node.get("availability") or {}
        if ctx.instances(node) >= 2 or avail.get("multi_az"):
            failover = avail.get("failover")
            if failover != "automatic":
                critical = node.get("type") in DatastoreTypes
                out.append(
                    result(
                        "ha.missing_failover",
                        "FAIL" if critical else "WARNING",
                        f"'{node.get('name')}' is redundant but failover mode is "
                        f"'{failover or 'undeclared'}' - a human may have to intervene at 3am.",
                        severity="critical" if critical else "high",
                        affected_nodes=[node["id"]],
                        suggested_actions=[
                            {
                                "action": "Declare availability.failover="
                                "automatic on redundant components"
                            }
                        ],
                    )
                )
    return out


# ---------------------------------------------------------------- performance


def r_perf_sync_expensive_dependency(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for e in ctx.edges:
        props = e.get("properties") or {}
        slow = props.get("expensive_ms")
        if isinstance(slow, (int, float)) and slow >= 300:
            if e.get("traffic_type", "sync_request") == "sync_request":
                out.append(
                    result(
                        "perf.sync_expensive_dependency",
                        "WARNING",
                        f"Edge '{e.get('id')}' adds ~{slow:.0f}ms synchronously on the request"
                        f"path.",
                        severity="high",
                        affected_edges=[str(e.get("id"))],
                        evidence=[f"declared expensive_ms={slow}"],
                        suggested_actions=[
                            {"action": "Move this work behind a queue/job, or cache its result"}
                        ],
                    )
                )
    return out


def r_perf_excessive_network_hops(ctx: EvalContext) -> list[dict[str, Any]]:
    longest = _longest_sync_path_len(ctx)
    if longest >= 6:
        return [
            result(
                "perf.excessive_network_hops",
                "WARNING",
                f"Longest synchronous path spans {longest} hops - latency stacks serially.",
                severity="low",
                confidence="medium",
                confidence_reason="hop count ignores real per-hop latencies",
            )
        ]
    return []


def _longest_sync_path_len(ctx: EvalContext) -> int:
    sync_adj: dict[str, list[str]] = {}
    for e in ctx.edges:
        if e.get("traffic_type", "sync_request") == "sync_request":
            sync_adj.setdefault(e["source"], []).append(e["target"])
    memo: dict[str, int] = {}

    def dfs(v: str, seen: set[str]) -> int:
        if v in memo:
            return memo[v]
        best = 1
        for nxt in sync_adj.get(v, []):
            if nxt in seen:
                continue
            best = max(best, 1 + dfs(nxt, seen | {v}))
        memo[v] = best
        return best

    return max((dfs(c["id"], {c["id"]}) for c in ctx.client_nodes()), default=0)


def r_perf_no_cache_high_read(ctx: EvalContext) -> list[dict[str, Any]]:
    read_rps_value, why = ctx.read_rps()
    if read_rps_value is None:
        return []
    if ctx.read_ratio is not None and ctx.read_ratio < 0.7:
        return []
    if not ctx.has_type(*DatastoreTypes):
        return []
    if ctx.cache_is_inline():
        return [
            result(
                "perf.no_cache_high_read",
                "PASS",
                "Read-heavy workload is absorbed by an inline cache.",
                evidence=[f"reads {read_rps_value:.0f}/s ({why})"],
            )
        ]
    if ctx.edge_cache_present():
        return [
            result(
                "perf.no_cache_high_read",
                "PASS",
                "Read-heavy workload is served from an edge CDN.",
                evidence=[
                    f"reads {read_rps_value:.0f}/s ({why})",
                    "cdn receives client traffic directly",
                ],
            )
        ]
    ratio_text = ctx.read_ratio if ctx.read_ratio is not None else "assumed 0.8"
    return [
        result(
            "perf.no_cache_high_read",
            "FAIL",
            f"Read-heavy workload ({read_rps_value:.0f} reads/s, "
            f"ratio {ratio_text}) hits storage with no inline cache.",
            severity="high",
            evidence=[f"read demand: {read_rps_value:.0f}/s ({why})"],
            suggested_actions=[
                {
                    "action": "Add redis between compute and the datastore (cache-aside)",
                    "tradeoffs": [
                        "staleness window equal to TTL",
                        "cache invalidation discipline required",
                    ],
                }
            ],
        )
    ]


def r_perf_slow_storage_critical_path(ctx: EvalContext) -> list[dict[str, Any]]:
    p95_target = _p95_target_ms(ctx)
    if p95_target is None:
        return []
    object_stores = ctx.nodes_of_type("object_storage")
    if not object_stores:
        return []
    for e in ctx.edges:
        src = ctx.nodes_by_id.get(e.get("source", ""))
        dst = ctx.nodes_by_id.get(e.get("target", ""))
        if src and dst and dst.get("type") == "object_storage":
            if e.get("traffic_type", "sync_request") == "sync_request":
                return [
                    result(
                        "perf.slow_storage_on_critical_path",
                        "WARNING",
                        f"Synchronous path reads/writes object storage while p95 target is"
                        f"{p95_target:.0f}ms.",
                        severity="medium",
                        affected_edges=[str(e.get("id"))],
                    )
                ]
    return []


def _p95_target_ms(ctx: EvalContext) -> float | None:
    for req in ctx.requirements:
        text = json_text(req.get("validation_rules"))
        if text and "p95" in text.lower():
            m = re.search(r"([0-9]+)\s*ms", text.lower())
            if m:
                return float(m.group(1))
    return None


# ---------------------------------------------------------------- consistency


def r_cons_replica_strong_reads(ctx: EvalContext) -> list[dict[str, Any]]:
    strong = _requires_strong_freshness(ctx)
    if not strong:
        return []
    out = []
    for store in ctx.nodes_of_type("postgresql", "mongodb"):
        avail = store.get("availability") or {}
        if avail.get("consistency_mode") == "eventual":
            out.append(
                result(
                    "cons.replica_for_strong_consistency",
                    "FAIL",
                    f"'{store.get('name')}' serves eventually-consistent reads while requirements"
                    f"demand strong freshness.",
                    severity="high",
                    affected_nodes=[store["id"]],
                )
            )
    return out


def _requires_strong_freshness(ctx: EvalContext) -> bool:
    keywords = ("strong", "immediately", "exactly-once", "read-your-writes")
    for req in ctx.requirements:
        text = json_text(req.get("description")) or ""
        rules = json_text(req.get("validation_rules")) or ""
        blob = (text + " " + rules).lower()
        if any(k in blob for k in keywords):
            return True
        if str(req.get("category", "")).lower() == "consistency":
            return True
    return False


def r_cons_cache_stale_strict(ctx: EvalContext) -> list[dict[str, Any]]:
    if not ctx.cache_is_inline():
        return []
    if not _requires_strong_freshness(ctx):
        return []
    return [
        result(
            "cons.cache_stale_strict_requirement",
            "WARNING",
            "Inline cache serves TTL-stale data while some requirements demand immediate"
            "freshness.",
            severity="high",
            suggested_actions=[
                {
                    "action": "Bypass cache for strict-read operations "
                    "or invalidate synchronously on write"
                }
            ],
        )
    ]


def r_cons_async_where_sync_required(ctx: EvalContext) -> list[dict[str, Any]]:
    sync_needed = ("confirm", "acknowledg", "synchronous", "immediate response")
    for req in ctx.requirements:
        text = (json_text(req.get("description")) or "").lower()
        if not any(k in text for k in sync_needed):
            continue
        for e in ctx.edges:
            if e.get("traffic_type") in ("async_event", "batch"):
                src_name = ctx.nodes_by_id.get(e["source"], {}).get("name", "?")
                dst_name = ctx.nodes_by_id.get(e["target"], {}).get("name", "?")
                path_desc = f"{src_name} -> {dst_name}"
                return [
                    result(
                        "cons.async_where_sync_required",
                        "FAIL",
                        f"Requirement '{req.get('id')}' expects synchronous confirmation but flow"
                        f"goes async: {path_desc}.",
                        severity="critical",
                        evidence=[f"requirement description: {json_text(req.get('description'))}"],
                        affected_edges=[str(e.get("id"))],
                        requirement_ids=[str(req.get("id"))],
                    )
                ]
    return []


# ---------------------------------------------------------------- reliability


def r_rel_retries_without_timeout(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for e in ctx.edges:
        props = e.get("properties") or {}
        if props.get("retry") and not props.get("timeout_ms"):
            out.append(
                result(
                    "rel.retries_without_timeout",
                    "FAIL",
                    f"Edge '{e.get('id')}' retries without a deadline - hangs multiply instead of"
                    f"healing.",
                    severity="high",
                    affected_edges=[str(e.get("id"))],
                    suggested_actions=[
                        {"action": "Set properties.timeout_ms below the caller's budget"}
                    ],
                )
            )
    return out


def r_rel_retries_without_backoff(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for e in ctx.edges:
        props = e.get("properties") or {}
        if props.get("retry") and props.get("timeout_ms") and props.get("backoff") != "exponential":
            out.append(
                result(
                    "rel.retries_without_backoff",
                    "WARNING",
                    f"Edge '{e.get('id')}' retries immediately - synchronized retry waves amplify"
                    f"outages.",
                    severity="medium",
                    affected_edges=[str(e.get("id"))],
                    suggested_actions=[
                        {"action": "Set properties.backoff='exponential' (with jitter)"}
                    ],
                )
            )
    return out


def r_rel_retry_amplification(ctx: EvalContext) -> list[dict[str, Any]]:
    edges_with_retry = [e for e in ctx.edges if (e.get("properties") or {}).get("retry")]
    if len(edges_with_retry) >= 3:
        ids = [str(e.get("id")) for e in edges_with_retry]
        return [
            result(
                "rel.retry_amplification",
                "WARNING",
                f"{len(ids)} sequential hops each retry - worst-case load multiplies across layers"
                f"during degradation.",
                severity="high",
                affected_edges=ids,
                evidence=[f"retrying edges: {', '.join(ids)}"],
                suggested_actions=[
                    {"action": "Budget retries end-to-end; keep retries at one layer per path"}
                ],
            )
        ]
    return []


def r_rel_missing_idempotency(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for queue in ctx.nodes_of_type(*QueueTypes):
        for consumer in ctx.queue_consumers(queue):
            if not ctx.prop(consumer, "idempotent_consumer", False):
                out.append(
                    result(
                        "rel.missing_idempotency",
                        "FAIL",
                        f"'{consumer.get('name')}' consumes at-least-once from"
                        f"'{queue.get('name')}' without idempotency declared.",
                        severity="high",
                        affected_nodes=[consumer["id"], queue["id"]],
                        suggested_actions=[
                            {
                                "action": "Set properties.idempotent_consumer=true "
                                "and dedupe by message key"
                            }
                        ],
                    )
                )
    return out


def r_rel_queue_without_dlq(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for queue in ctx.nodes_of_type(*QueueTypes):
        props = queue.get("properties") or {}
        if not props.get("dlq"):
            consumers = ctx.queue_consumers(queue)
            if consumers:
                out.append(
                    result(
                        "rel.queue_without_dlq",
                        "WARNING",
                        f"'{queue.get('name')}' has consumers but no dead-letter queue - poison"
                        f"messages block the head.",
                        severity="medium",
                        affected_nodes=[queue["id"]],
                        suggested_actions=[
                            {"action": "Set properties.dlq=true and alarm on DLQ depth"}
                        ],
                    )
                )
    return out


# ---------------------------------------------------------------- security


def r_sec_public_database(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    client_ids = {c["id"] for c in ctx.client_nodes()}
    for e in ctx.edges:
        if e.get("source") in client_ids:
            dst = ctx.nodes_by_id.get(e.get("target", ""))
            if dst and dst.get("type") in DatastoreTypes:
                out.append(
                    result(
                        "sec.public_database",
                        "FAIL",
                        f"Clients connect directly to datastore '{dst.get('name')}' - no private"
                        f"network boundary.",
                        severity="critical",
                        affected_nodes=[dst["id"]],
                        affected_edges=[str(e.get("id"))],
                        suggested_actions=[
                            {"action": "Route data access through an internal service/API tier"}
                        ],
                    )
                )
    return out


def r_sec_missing_authentication(ctx: EvalContext) -> list[dict[str, Any]]:
    public_apis = ctx.nodes_of_type("api")
    if not public_apis:
        return []
    unauthed = [a for a in public_apis if not ctx.prop(a, "auth", False)]
    if unauthed:
        return [
            result(
                "sec.missing_authentication",
                "FAIL",
                "API tier accepts requests without authentication configured.",
                severity="high",
                affected_nodes=[a["id"] for a in unauthed],
                suggested_actions=[{"action": "Enable auth (token/JWT/OAuth) at the API boundary"}],
            )
        ]
    return [
        result("sec.missing_authentication", "PASS", "Authentication enabled on the API boundary.")
    ]


def r_sec_missing_authorization(ctx: EvalContext) -> list[dict[str, Any]]:
    multi_user = any(
        "user" in (json_text(req.get("description")) or "").lower() for req in ctx.requirements
    )
    if not multi_user:
        return []
    apis = ctx.nodes_of_type("api")
    missing_authz = [a for a in apis if not ctx.prop(a, "authorization_checks", False)]
    if missing_authz:
        return [
            result(
                "sec.missing_authorization",
                "WARNING",
                "Multi-user flows exist but no authorization checks are declared on services.",
                severity="medium",
                affected_nodes=[a["id"] for a in missing_authz],
            )
        ]
    return []


def r_sec_unencrypted_sensitive_flow(ctx: EvalContext) -> list[dict[str, Any]]:
    plaintext = {"http", "tcp", ""}
    sensitive_types = DatastoreTypes | QueueTypes | ComputeTypes
    out = []
    for e in ctx.edges:
        protocol = str(e.get("protocol") or "").lower()
        src = ctx.nodes_by_id.get(e.get("source", ""))
        dst = ctx.nodes_by_id.get(e.get("target", ""))
        if not src or not dst:
            continue
        crosses_tiers = (src.get("type") in sensitive_types) != (dst.get("type") in sensitive_types)
        if crosses_tiers and protocol in plaintext:
            out.append(
                result(
                    "sec.unencrypted_sensitive_flow",
                    "WARNING",
                    f"Edge '{e.get('id')}' ({src.get('name')} -> {dst.get('name')}) uses protocol"
                    f"'{protocol or 'unspecified'}'.",
                    severity="high",
                    affected_edges=[str(e.get("id"))],
                    suggested_actions=[{"action": "Switch protocol to https/tls/grpc"}],
                )
            )
    return out


def r_sec_missing_secrets_management(ctx: EvalContext) -> list[dict[str, Any]]:
    offenders = []
    for node in ctx.nodes:
        text = json_text(node.get("properties") or {}) or ""
        lowered = text.lower()
        for token in ("password=", "secret=", "api_key="):
            if token in lowered and not ctx.prop(node, "secrets_managed", False):
                offenders.append(node)
                break
    if offenders:
        return [
            result(
                "sec.missing_secrets_management",
                "WARNING",
                "Credentials appear embedded in component properties rather than a secret store.",
                severity="medium",
                affected_nodes=[n["id"] for n in offenders],
                suggested_actions=[
                    {"action": "Reference a secrets manager; never inline credentials"}
                ],
            )
        ]
    return []


# ---------------------------------------------------------------- observability


def r_obs_no_metrics(ctx: EvalContext) -> list[dict[str, Any]]:
    instrumented = [
        n
        for n in ctx.nodes
        if n.get("type") != "client" and ctx.prop(n, "metrics", False)
    ]
    if not ctx.nodes:
        return []
    if instrumented:
        return [
            result(
                "obs.no_metrics",
                "PASS",
                f"{len(instrumented)} component(s) export metrics.",
            )
        ]
    return [
        result(
            "obs.no_metrics",
            "WARNING",
            "No component exports metrics - failures will be invisible until users report them.",
            severity="medium",
        )
    ]


def r_obs_no_logs(ctx: EvalContext) -> list[dict[str, Any]]:
    logged = [n for n in ctx.nodes if n.get("type") != "client" and ctx.prop(n, "logs", False)]
    if not ctx.nodes:
        return []
    if logged:
        return []
    return [
        result(
            "obs.no_logs",
            "WARNING",
            "No structured logging declared anywhere; incident forensics will be guesswork.",
            severity="low",
        )
    ]


def r_obs_no_tracing(ctx: EvalContext) -> list[dict[str, Any]]:
    traced = [n for n in ctx.nodes if ctx.prop(n, "tracing", False)]
    src_hops = {e.get("source") for e in ctx.edges}
    dst_hops = {e.get("target") for e in ctx.edges}
    multi_hop = len(src_hops) + len(dst_hops) >= 4
    if not multi_hop:
        return []
    if traced:
        return []
    return [
        result(
            "obs.no_tracing",
            "WARNING",
            "Multi-hop system without distributed tracing - latency attribution will be manual"
            "archaeology.",
            severity="low",
        )
    ]


def r_obs_no_alerts(ctx: EvalContext) -> list[dict[str, Any]]:
    target = ctx.availability_target()
    alerting = any(ctx.prop(n, "alerts", False) for n in ctx.nodes)
    if alerting:
        return [result("obs.no_alerts_critical", "PASS", "Alerting path declared.")]
    if target is not None and target >= 99.9:
        return [
            result(
                "obs.no_alerts_critical",
                "FAIL",
                f"Availability target {target}% but no alerting configured - nobody gets paged.",
                severity="medium",
            )
        ]
    return []


# ---------------------------------------------------------------- edge semantics


def r_edge_missing_traffic_type(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for i, e in enumerate(ctx.graph.get("_raw_edges", [])):
        if "traffic_type" not in e:
            out.append(
                result(
                    "edge.missing_traffic_type",
                    "WARNING",
                    f"Edge #{i} lacks explicit traffic_type semantics (normalized to"
                    f"sync_request).",
                    severity="low",
                    confidence="medium",
                    confidence_reason="normalizer filled a default; author intent unknown",
                )
            )
    return out


def r_edge_cache_not_inline(ctx: EvalContext) -> list[dict[str, Any]]:
    if not ctx.has_type(*CacheTypes):
        return []
    if ctx.cache_is_inline():
        return []
    caches = ctx.nodes_of_type(*CacheTypes)
    return [
        result(
            "edge.cache_not_inline",
            "WARNING",
            "Cache exists but is not connected between compute and a datastore - it does nothing.",
            severity="medium",
            affected_nodes=[c["id"] for c in caches],
            suggested_actions=[
                {"action": "Wire compute -> cache -> datastore so reads can be served from cache"}
            ],
        )
    ]


def r_edge_queue_unconsumed(ctx: EvalContext) -> list[dict[str, Any]]:
    out = []
    for queue in ctx.nodes_of_type(*QueueTypes):
        if not ctx.queue_consumers(queue):
            out.append(
                result(
                    "edge.queue_unconsumed",
                    "FAIL",
                    f"'{queue.get('name')}' ingests events with no consumer connected downstream.",
                    severity="high",
                    affected_nodes=[queue["id"]],
                )
            )
    return out


def r_edge_cdn_unused_static(ctx: EvalContext) -> list[dict[str, Any]]:
    cdns = ctx.nodes_of_type("cdn")
    if not cdns:
        return []
    used = any(
        ctx.nodes_by_id.get(e.get("target", ""), {}).get("type") == "cdn"
        or ctx.nodes_by_id.get(e.get("source", ""), {}).get("type") == "cdn"
        for e in ctx.edges
    )
    if used:
        return []
    return [
        result(
            "edge.cdn_unused_static",
            "WARNING",
            "CDN present but disconnected from the serving path - static assets still hit origin.",
            severity="low",
            affected_nodes=[c["id"] for c in cdns],
        )
    ]


RULES: dict[str, Callable[[EvalContext], list[dict[str, Any]]]] = {
    "graph.disconnected_required_component": r_graph_disconnected_required,
    "graph.invalid_edge": r_graph_invalid_edge,
    "graph.missing_source": r_graph_missing_source,
    "graph.missing_destination": r_graph_missing_destination,
    "graph.inappropriate_cycle": r_graph_inappropriate_cycle,
    "graph.no_ingress": r_graph_no_ingress,
    "graph.no_data_store_required": r_graph_no_data_store,
    "scale.single_compute_high_traffic": r_scale_single_compute_high_traffic,
    "scale.db_write_bottleneck": r_scale_db_write_bottleneck,
    "scale.db_read_bottleneck": r_scale_db_read_bottleneck,
    "scale.insufficient_worker_capacity": r_scale_insufficient_worker_capacity,
    "scale.queue_consumer_shortage": r_scale_queue_consumer_shortage,
    "scale.partition_hot_spot": r_scale_partition_hot_spot,
    "scale.missing_load_balancing": r_scale_missing_load_balancing,
    "scale.missing_horizontal_scaling": r_scale_missing_horizontal_scaling,
    "ha.single_database": r_ha_single_database,
    "ha.single_cache": r_ha_single_cache,
    "ha.single_compute_node": r_ha_single_compute_node,
    "ha.single_region": r_ha_single_region,
    "ha.single_load_balancer": r_ha_single_load_balancer,
    "ha.missing_failover": r_ha_missing_failover,
    "perf.sync_expensive_dependency": r_perf_sync_expensive_dependency,
    "perf.excessive_network_hops": r_perf_excessive_network_hops,
    "perf.no_cache_high_read": r_perf_no_cache_high_read,
    "perf.slow_storage_on_critical_path": r_perf_slow_storage_critical_path,
    "cons.replica_for_strong_consistency": r_cons_replica_strong_reads,
    "cons.cache_stale_strict_requirement": r_cons_cache_stale_strict,
    "cons.async_where_sync_required": r_cons_async_where_sync_required,
    "rel.retries_without_timeout": r_rel_retries_without_timeout,
    "rel.retries_without_backoff": r_rel_retries_without_backoff,
    "rel.retry_amplification": r_rel_retry_amplification,
    "rel.missing_idempotency": r_rel_missing_idempotency,
    "rel.queue_without_dlq": r_rel_queue_without_dlq,
    "sec.public_database": r_sec_public_database,
    "sec.missing_authentication": r_sec_missing_authentication,
    "sec.missing_authorization": r_sec_missing_authorization,
    "sec.unencrypted_sensitive_flow": r_sec_unencrypted_sensitive_flow,
    "sec.missing_secrets_management": r_sec_missing_secrets_management,
    "obs.no_metrics": r_obs_no_metrics,
    "obs.no_logs": r_obs_no_logs,
    "obs.no_tracing": r_obs_no_tracing,
    "obs.no_alerts_critical": r_obs_no_alerts,
    "edge.missing_traffic_type": r_edge_missing_traffic_type,
    "edge.cache_not_inline": r_edge_cache_not_inline,
    "edge.queue_unconsumed": r_edge_queue_unconsumed,
    "edge.cdn_unused_static": r_edge_cdn_unused_static,
}
