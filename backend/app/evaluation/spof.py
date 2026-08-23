"""Single-point-of-failure and bottleneck detection.

SPOF: any non-client node with <2 effective instances whose removal would
disconnect a datastore/queue/cache from the serving path (or that IS the
sole instance of its kind on the path).

Bottleneck: per-stage capacity vs estimated demand using catalog defaults.
"""

from __future__ import annotations

from typing import Any

from app.evaluation.context import DatastoreTypes, EvalContext


def detect_spofs(ctx: EvalContext) -> list[dict[str, Any]]:
    spofs: list[dict[str, Any]] = []
    for node in ctx.nodes:
        ntype = str(node.get("type") or "")
        if ntype == "client":
            continue
        if ctx.instances(node) >= 2:
            continue
        blast = _blast_radius(ctx, node)
        if blast is None:
            continue
        kind, radius = blast
        spofs.append(
            {
                "node_id": node["id"],
                "blast_radius": radius,
                "reason": (
                    f"Sole {ntype} '{node.get('name')}' - "
                    f"{kind} fails completely if it goes down."
                ),
            }
        )
    return spofs


def _blast_radius(ctx: EvalContext, node: dict[str, Any]) -> tuple[str, str] | None:
    """(what breaks, severity) or None if redundant/not load-bearing."""
    nid = node["id"]
    reachable_without = _reachable_excluding(ctx, nid)
    critical_types = DatastoreTypes | {"load_balancer", "api"}
    datastores = [d for d in ctx.nodes_of_type(*DatastoreTypes) if d["id"] != nid]

    # If removing this node disconnects every datastore from clients -> total.
    if datastores and not any(d["id"] in reachable_without for d in datastores):
        return ("data access", "total")

    # Sole API in front of reachable datastores.
    if node.get("type") == "api" and len(ctx.nodes_of_type("api")) == 1:
        return ("request serving", "total")

    # Sole LB with everything behind it.
    if node.get("type") == "load_balancer" and len(ctx.nodes_of_type("load_balancer")) == 1:
        behind = [n for n in ctx.nodes if n.get("type") in critical_types and n["id"] != nid]
        if behind:
            return ("traffic distribution", "major")

    if node.get("type") in ("redis", "kafka", "rabbitmq", "worker"):
        return (f"{node.get('type')} services", "partial")
    return None


def _reachable_excluding(ctx: EvalContext, excluded_id: str) -> set[str]:
    seen: set[str] = set()
    frontier = [c["id"] for c in ctx.client_nodes() if c["id"] != excluded_id]
    while frontier:
        current = frontier.pop()
        for e in ctx.edges:
            nxt = None
            if e.get("source") == current:
                nxt = e.get("target")
            elif e.get("target") == current:
                nxt = e.get("source")
            if (
                nxt
                and nxt != excluded_id
                and nxt in ctx.nodes_by_id
                and nxt not in seen
            ):
                seen.add(nxt)
                frontier.append(nxt)
    return seen


def detect_bottlenecks(ctx: EvalContext) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    demand = ctx.demand_rps()
    read_value, why = ctx.read_rps()
    write_value, wwhy = ctx.write_rps()

    for store in ctx.nodes_of_type("postgresql", "mongodb"):
        read_cap = (ctx.capacity_of(store, "safe_reads_per_sec") or 0.0) * max(
            1, ctx.instances(store)
        )
        write_cap = (ctx.capacity_of(store, "safe_writes_per_sec") or 0.0) * max(
            1, ctx.instances(store)
        )
        cache_factor = 0.1 if ctx.cache_is_inline() else 1.0
        eff_reads = (read_value or 0.0) * cache_factor
        utilization = max(
            eff_reads / read_cap if read_cap else 0.0,
            (write_value or 0.0) / write_cap if write_cap else 0.0,
        )
        if utilization > 0.8:
            dominant = read_cap if eff_reads >= (write_value or 0.0) else write_cap
            out.append(
                {
                    "node_id": store["id"],
                    "demand": round(max(eff_reads, write_value or 0.0), 1),
                    "capacity": round(dominant, 1),
                    "unit": "ops/s",
                    "path": [store["id"]],
                    "reason": f"'{store.get('name')}' at ~{utilization:.0%} of safe capacity "
                    f"(reads {why}; writes {wwhy}).",
                }
            )

    apis = ctx.nodes_of_type("api")
    if apis and demand is not None:
        cap = float(
            (ctx.catalog.get("api") or {}).get("capacity_defaults", {}).get(
                "rps_per_instance", 1000
            )
        )
        total = cap * ctx.total_instances("api")
        if total and demand / total > 0.8:
            out.append(
                {
                    "node_id": apis[0]["id"],
                    "demand": round(demand, 1),
                    "capacity": round(total, 1),
                    "unit": "rps",
                    "path": [a["id"] for a in apis],
                    "reason": f"API tier at ~{demand / total:.0%} of rated capacity.",
                }
            )
    return out
