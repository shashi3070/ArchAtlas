"""Evaluation context: normalized accessors over a canonical graph + catalog.

All rule functions receive an EvalContext and must stay pure - no I/O, no
clock, no randomness (determinism is a product requirement).
"""

from __future__ import annotations

import json
import re
from typing import Any

DatastoreTypes = frozenset({"postgresql", "mongodb", "object_storage"})
ComputeTypes = frozenset({"api", "worker"})
QueueTypes = frozenset({"kafka", "rabbitmq"})
CacheTypes = frozenset({"redis"})

_REQ_RPS_RE = re.compile(r"rps\s*(?:>=|<=|>|<|=)\s*([0-9][0-9_,]*)", re.IGNORECASE)


class EvalContext:
    def __init__(self, graph: dict[str, Any], catalog: dict[str, dict[str, Any]]) -> None:
        self.graph = graph
        self.catalog = catalog
        self.nodes: list[dict[str, Any]] = graph.get("nodes", [])
        self.edges: list[dict[str, Any]] = graph.get("edges", [])
        self.nodes_by_id: dict[str, dict[str, Any]] = {n["id"]: n for n in self.nodes}
        self.requirements: list[dict[str, Any]] = graph.get("requirements", [])
        tm = graph.get("traffic_model") or {}
        self.rps: float | None = _as_number(tm.get("rps"))
        rr = _as_number(tm.get("read_ratio"))
        wr = _as_number(tm.get("write_ratio"))
        self.read_ratio: float | None
        if rr is not None and 0 <= rr <= 1:
            self.read_ratio = rr
        elif wr is not None and 0 <= wr <= 1:
            self.read_ratio = round(1 - wr, 4)
        else:
            self.read_ratio = None
        self.required_components: list[str] = list(
            (graph.get("metadata") or {}).get("required_components") or []
        )

    # ---------- demand model ----------

    def demand_rps(self) -> float | None:
        """Best-effort demand estimate; None means 'unknown' (never guess)."""
        if self.rps is not None:
            return self.rps
        for req in self.requirements:
            match = _REQ_RPS_RE.search(str(req.get("validation_rules") or ""))
            if match:
                return float(match.group(1).replace("_", "").replace(",", ""))
        return None

    def read_rps(self) -> tuple[float | None, str]:
        """Returns (value, confidence_reason)."""
        demand = self.demand_rps()
        if demand is None:
            return None, "no traffic_model.rps and no rps validation rule declared"
        ratio = self.read_ratio
        reason = (
            "traffic_model.read_ratio"
            if self.rps is not None and self.read_ratio is not None
            else "assumed default read_ratio"
        )
        value = demand * (ratio if ratio is not None else 0.8)
        return value, reason

    def write_rps(self) -> tuple[float | None, str]:
        demand = self.demand_rps()
        if demand is None:
            return None, "no traffic_model.rps and no rps validation rule declared"
        ratio = self.read_ratio
        value = demand * ((1 - ratio) if ratio is not None else 0.2)
        reason = (
            "traffic_model.write_ratio"
            if self.rps is not None and self.read_ratio is not None
            else "assumed default write_ratio"
        )
        return value, reason

    # ---------- node helpers ----------

    def nodes_of_type(self, *types: str) -> list[dict[str, Any]]:
        return [n for n in self.nodes if n.get("type") in types]

    def has_type(self, *types: str) -> bool:
        return any(n.get("type") in types for n in self.nodes)

    def instances(self, node: dict[str, Any]) -> int:
        avail = node.get("availability") or {}
        replicas = avail.get("replicas")
        if isinstance(replicas, int) and replicas >= 1:
            return replicas
        entry = self.catalog_entry(node)
        defaults = (entry or {}).get("capacity_defaults") or {}
        di = defaults.get("default_instances")
        if isinstance(di, int) and di >= 1:
            return di
        dr = defaults.get("default_replicas")
        if isinstance(dr, int) and dr >= 0:
            return max(1, dr + 1)  # primary + replicas
        return 1

    def total_instances(self, *types: str) -> int:
        return sum(self.instances(n) for n in self.nodes_of_type(*types))

    def capacity_of(self, node: dict[str, Any], key: str) -> float | None:
        override = (node.get("capacity") or {}).get(key)
        if isinstance(override, (int, float)):
            return float(override)
        entry = self.catalog_entry(node)
        value = ((entry or {}).get("capacity_defaults") or {}).get(key)
        return float(value) if isinstance(value, (int, float)) else None

    def prop(self, node_or_edge: dict[str, Any], key: str, default: Any = None) -> Any:
        props = node_or_edge.get("properties") or {}
        value = props.get(key, default)
        return value

    def catalog_entry(self, node: dict[str, Any]) -> dict[str, Any] | None:
        ctype = str(node.get("type") or "")
        return self.catalog.get(ctype)

    def availability_target(self) -> float | None:
        """Parse availability target like 'availability >= 99.9' from requirements."""
        for req in self.requirements:
            text = json_str(req.get("validation_rules"))
            if text and "availability" in text.lower():
                m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
                if m:
                    return float(m.group(1))
        return None

    # ---------- topology helpers ----------

    def out_edges(self, node_id: str) -> list[dict[str, Any]]:
        return [e for e in self.edges if e.get("source") == node_id]

    def in_edges(self, node_id: str) -> list[dict[str, Any]]:
        return [e for e in self.edges if e.get("target") == node_id]

    def edges_between(
        self,
        a_types: set[str] | frozenset[str],
        b_types: set[str] | frozenset[str],
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Edges whose source type is in a_types and target type in b_types."""
        out: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for e in self.edges:
            src = self.nodes_by_id.get(e.get("source", ""))
            dst = self.nodes_by_id.get(e.get("target", ""))
            if src and dst and src.get("type") in a_types and dst.get("type") in b_types:
                out.append((src, dst))
        return out

    def client_nodes(self) -> list[dict[str, Any]]:
        clients = self.nodes_of_type("client")
        return clients if clients else []

    def reachable_from_clients(self) -> set[str]:
        """Node ids reachable following ANY edge direction from clients."""
        seen: set[str] = set()
        frontier = [c["id"] for c in self.client_nodes()]
        while frontier:
            current = frontier.pop()
            for e in self.edges:
                nxt = None
                if e.get("source") == current:
                    nxt = e.get("target")
                elif e.get("target") == current:
                    nxt = e.get("source")
                if nxt and nxt in self.nodes_by_id and nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
        return seen

    def sync_cycle_exists(self) -> list[list[str]]:
        """Find cycles composed ONLY of sync_request edges."""
        sync_adj: dict[str, list[str]] = {}
        for e in self.edges:
            if e.get("traffic_type", "sync_request") == "sync_request":
                sync_adj.setdefault(e["source"], []).append(e["target"])
        cycles: list[list[str]] = []
        for start in sorted(sync_adj):
            _find_cycles_from(sync_adj, start, start, [start], {start}, cycles)
        return cycles

    def cache_is_inline(self) -> bool:
        """A cache counts as inline when it bridges compute<->datastore both ways."""
        caches = {c["id"] for c in self.nodes_of_type(*CacheTypes)}
        if not caches:
            return False
        datastores = {d["id"] for d in self.nodes_of_type(*DatastoreTypes - {"object_storage"})}
        compute = {a["id"] for a in self.nodes_of_type(*ComputeTypes)}
        cache_to_ds = any(
            e["source"] in caches and e["target"] in datastores for e in self.edges
        )
        compute_to_cache = any(
            e["source"] in compute and e["target"] in caches for e in self.edges
        )
        ds_to_cache = any(
            e["source"] in datastores and e["target"] in caches for e in self.edges
        )
        return cache_to_ds and (compute_to_cache or ds_to_cache)

    def edge_cache_present(self) -> bool:
        """A CDN directly fronting clients is a read cache at the edge."""
        cdns = {c["id"] for c in self.nodes_of_type("cdn")}
        if not cdns:
            return False
        return any(e["source"] in {c["id"] for c in self.client_nodes()} for e in self.edges
                   if e["target"] in cdns)

    def queue_consumers(self, queue_node: dict[str, Any]) -> list[dict[str, Any]]:
        consumer_types = ComputeTypes
        return [
            self.nodes_by_id[e["target"]]
            for e in self.out_edges(queue_node["id"])
            if e.get("target") in self.nodes_by_id
            and self.nodes_by_id[e["target"]].get("type") in consumer_types
        ]


def _as_number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and value >= 0 else None


def _find_cycles_from(
    adj: dict[str, list[str]],
    start: str,
    current: str,
    path: list[str],
    visited: set[str],
    cycles: list[list[str]],
) -> None:
    """DFS collecting up to 5 cycles that return to `start` (lexicographic guard)."""
    if len(cycles) >= 5:
        return
    for nxt in adj.get(current, []):
        if nxt == start and len(path) > 1:
            cycles.append(list(path))
        elif nxt not in visited and nxt >= start:
            path.append(nxt)
            visited.add(nxt)
            _find_cycles_from(adj, start, nxt, path, visited, cycles)
            path.pop()
            visited.discard(nxt)


def json_str(value: Any) -> str | None:
    """Best-effort serialization of arbitrary JSON-ish values for text scans."""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        return json.dumps(value, default=str)
    return None
