"""Shared builders for evaluation tests."""

from __future__ import annotations

from typing import Any

from app.content.loader import load_catalog
from app.evaluation.context import EvalContext


def cat() -> dict[str, dict[str, Any]]:
    return load_catalog()


def n(
    nid: str,
    ntype: str,
    name: str | None = None,
    *,
    replicas: int | None = None,
    multi_az: bool = False,
    failover: str | None = None,
    props: dict[str, Any] | None = None,
    capacity: dict[str, Any] | None = None,
    avail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": nid,
        "type": ntype,
        "name": name or nid,
        "position": {"x": 0, "y": 0},
        "properties": props or {},
        "availability": {},
        "capacity": capacity or {},
        "deployment": {},
    }
    if replicas is not None:
        node["availability"]["replicas"] = replicas
    if multi_az:
        node["availability"]["multi_az"] = True
    if failover:
        node["availability"]["failover"] = failover
    node["availability"].update(avail or {})
    return node


def e(
    eid: str,
    src: str,
    dst: str,
    props: dict[str, Any] | None = None,
    **kw: Any,
) -> dict[str, Any]:
    edge: dict[str, Any] = {"id": eid, "source": src, "target": dst}
    edge["properties"] = props or {}
    edge.update(kw)
    return edge


def g(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"id": "t", "version": 1, "nodes": nodes, "edges": edges}
    base.update(extra)
    return base


def make_ctx(graph: dict[str, Any], cat: dict[str, dict[str, Any]]) -> EvalContext:
    return EvalContext(graph, cat)


def statuses(ctx_result: list[dict[str, Any]]) -> dict[str, str]:
    return {r["rule_id"]: r["status"] for r in ctx_result}


_STATUS_ORDER = {"INFO": 0, "PASS": 0, "UNKNOWN": 1, "WARNING": 2, "FAIL": 3}


def run_rules(cat: dict[str, dict[str, Any]], graph: dict[str, Any]) -> dict[str, Any]:
    """Run all rules against a graph; returns {rule_id: worst status emitted}."""
    from app.evaluation.rules import RULES

    ctx = make_ctx(graph, cat)
    out: dict[str, str] = {}
    for rule_id, fn in RULES.items():
        for result_item in fn(ctx):
            status = result_item["status"]
            if rule_id not in out or _STATUS_ORDER[status] > _STATUS_ORDER[out[rule_id]]:
                out[rule_id] = status
    return out


CLIENT_LB_API_DB = g(
    [
        n("c", "client"),
        n("lb", "load_balancer", replicas=2, failover="automatic"),
        n("api", "api", replicas=3, multi_az=True, failover="automatic",
          props={"auth": True, "metrics": True, "logs": True}),
        n("db", "postgresql", replicas=3, multi_az=True, failover="automatic"),
    ],
    [
        e("e1", "c", "lb"),
        e("e2", "lb", "api", protocol="https"),
        e("e3", "api", "db", protocol="https"),
    ],
)
