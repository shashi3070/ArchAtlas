"""Requirement mapping: parse machine-checkable expressions into outcomes.

Supported expressions (subset promised by the requirement schema):
  rps >= 100000          -> capacity check against API tier + store headroom
  p95 <= 200ms           -> heuristic hop-latency estimate vs target
  availability >= 99.9   -> redundancy/failover posture vs nines
  durability >= 11       -> storage replication posture
Outcomes never claim more than the evidence supports: not_evaluable exists
for a reason and carries the missing-input reason.
"""

from __future__ import annotations

import re
from typing import Any

from app.evaluation.context import ClientTypes, EvalContext, RedundancyCriticalTypes

_RPS_RE = re.compile(r"rps\s*(>=|<=|>|<)\s*([0-9][0-9_,]*)", re.IGNORECASE)
_P95_RE = re.compile(r"p95\s*(<=|<)\s*([0-9]+)\s*ms", re.IGNORECASE)
_AVAIL_RE = re.compile(r"availability\s*(>=|>)\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
_DUR_RE = re.compile(r"durability\s*(>=|>)\s*([0-9]+)", re.IGNORECASE)


def map_requirements(ctx: EvalContext) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for req in ctx.requirements:
        rid = str(req.get("id", "?"))
        rules = req.get("validation_rules") or []
        if isinstance(rules, str):
            rules = [rules]
        if not rules:
            outcomes.append(
                {
                    "requirement_id": rid,
                    "status": "not_evaluable",
                    "confidence": "high",
                    "reason": "requirement declares no validation_rules",
                }
            )
            continue
        # Aggregate per-expression outcomes; worst wins.
        expr_outcomes = [
            _evaluate_expression(ctx, expr) for expr in [str(r) for r in rules]
        ]
        order = {"violated": 0, "at_risk": 1, "satisfied": 2, "not_evaluable": 3}
        expr_outcomes.sort(key=lambda o: order[o["status"]])
        worst = expr_outcomes[0]
        merged: dict[str, Any] = {
            "requirement_id": rid,
            "status": worst["status"],
            "confidence": worst["confidence"],
            "reason": "; ".join(
                f"{expr}: {o.get('reason') or o['status']}"
                for expr, o in zip([str(r) for r in rules], expr_outcomes, strict=False)
            ),
        }
        evidence: list[str] = []
        for o in expr_outcomes:
            evidence.extend(o.get("evidence") or [])
        if evidence:
            merged["evidence"] = evidence[:8]
        outcomes.append(merged)
    return outcomes


def _evaluate_expression(ctx: EvalContext, expression: str) -> dict[str, Any]:
    m = _RPS_RE.search(expression)
    if m:
        return _check_rps(ctx, float(m.group(2).replace(",", "").replace("_", "")))
    m = _P95_RE.search(expression)
    if m:
        return _check_p95(ctx, float(m.group(2)))
    m = _AVAIL_RE.search(expression)
    if m:
        return _check_availability(ctx, float(m.group(2)))
    m = _DUR_RE.search(expression)
    if m:
        return _check_durability(ctx, int(m.group(2)))
    return {
        "status": "not_evaluable",
        "confidence": "high",
        "reason": f"unsupported expression '{expression}'",
    }


def _check_rps(ctx: EvalContext, target: float) -> dict[str, Any]:
    demand = ctx.demand_rps()
    apis = ctx.nodes_of_type("api")
    if demand is None or not apis:
        return {
            "status": "not_evaluable",
            "confidence": "low",
            "reason": "needs traffic_model.rps and at least one api node",
        }
    api_caps = (ctx.catalog.get("api") or {}).get("capacity_defaults", {})
    default_cap = float(api_caps.get("rps_per_instance", 1000))
    # Per-node capacity overrides win; catalog default is the fallback.
    total = 0.0
    fleet: list[str] = []
    for api in apis:
        per_instance = float(
            (api.get("capacity") or {}).get("rps_per_instance", default_cap)
        )
        sub = per_instance * ctx.instances(api)
        total += sub
        fleet.append(f"{api['id']}: {sub:.0f}")
    if total >= target * 1.2:
        return {
            "status": "satisfied",
            "confidence": "medium",
            "evidence": [f"API tier rated {total:.0f} rps vs target {target:.0f}"] + fleet,
            "reason": None,
        }
    if total >= target:
        return {
            "status": "at_risk",
            "confidence": "medium",
            "evidence": [
                f"API tier rated {total:.0f} rps - only {total / target:.1f}x target"
            ]
            + fleet,
            "reason": "headroom below 1.2x target",
        }
    return {
        "status": "violated",
        "confidence": "medium",
        "evidence": [f"API tier rated {total:.0f} rps < target {target:.0f}"] + fleet,
        "reason": None,
    }


def _check_p95(ctx: EvalContext, target_ms: float) -> dict[str, Any]:
    hops = _longest_sync_hops(ctx)
    base = float((ctx.catalog.get("api") or {}).get("capacity_defaults", {}).get("p95_base_ms", 50))
    estimate = hops * base
    if estimate <= target_ms:
        return {
            "status": "satisfied",
            "confidence": "low",
            "evidence": [f"estimate {estimate:.0f}ms = {hops} hops x {base:.0f}ms"],
            "reason": "coarse hop-count model; measure with real traces",
        }
    if estimate <= target_ms * 1.5:
        return {
            "status": "at_risk",
            "confidence": "low",
            "evidence": [f"estimate {estimate:.0f}ms vs {target_ms:.0f}ms target"],
            "reason": "hop model within 50% of target",
        }
    return {
        "status": "violated",
        "confidence": "low",
        "evidence": [f"estimate {estimate:.0f}ms >> {target_ms:.0f}ms target ({hops} serial hops)"],
        "reason": None,
    }


def _longest_sync_hops(ctx: EvalContext) -> int:
    sync_adj: dict[str, list[str]] = {}
    for e in ctx.edges:
        if e.get("traffic_type", "sync_request") == "sync_request":
            sync_adj.setdefault(e["source"], []).append(e["target"])
    memo: dict[str, int] = {}

    def dfs(v: str, seen: set[str]) -> int:
        if v in memo:
            return memo[v]
        best = 0
        for nxt in sync_adj.get(v, []):
            if nxt in seen:
                continue
            best = max(best, 1 + dfs(nxt, seen | {v}))
        memo[v] = best
        return best

    return max((dfs(c["id"], {c["id"]}) for c in ctx.client_nodes()), default=0)


def _check_availability(ctx: EvalContext, target_nines: float) -> dict[str, Any]:
    critical_single = []
    automatic_failover_count = 0
    redundant_critical = 0
    for node in ctx.nodes:
        if node.get("type") in ClientTypes:
            continue
        avail = node.get("availability") or {}
        instances = ctx.instances(node)
        if node.get("type") in RedundancyCriticalTypes:
            if instances >= 2 or avail.get("multi_az"):
                redundant_critical += 1
                if avail.get("failover") == "automatic":
                    automatic_failover_count += 1
            else:
                critical_single.append(node)
    evidence = [
        f"{redundant_critical} critical component(s) redundant, "
        f"{len(critical_single)} single-instance"
    ]
    if not critical_single and redundant_critical > 0 and automatic_failover_count >= 1:
        status = "satisfied" if target_nines <= 99.99 else "at_risk"
        return {"status": status, "confidence": "medium", "evidence": evidence, "reason": None}
    if len(critical_single) >= 1:
        return {
            "status": "violated",
            "confidence": "medium",
            "evidence": evidence + [f"single points: {[n['name'] for n in critical_single]}"],
            "reason": None,
        }
    return {
        "status": "at_risk",
        "confidence": "medium",
        "evidence": evidence,
        "reason": "no automatic failover declared on redundant components",
    }


def _check_durability(ctx: EvalContext, nines: int) -> dict[str, Any]:
    stores = ctx.nodes_of_type(*{"object_storage"} | {"postgresql", "mongodb"})
    if not stores:
        return {
            "status": "violated",
            "confidence": "medium",
            "evidence": ["no durable storage component present"],
            "reason": None,
        }
    best = max(
        int(
            ((ctx.catalog_entry(s) or {}).get("capacity_defaults") or {}).get(
                "durability_nines", 0
            )
        )
        for s in stores
    )
    replicated = any(ctx.instances(s) >= 2 for s in stores)
    evidence = [f"durability nines from catalog: {best}; replicated: {replicated}"]
    if best >= nines:
        return {"status": "satisfied", "confidence": "medium", "evidence": evidence, "reason": None}
    if best >= nines - 3 and replicated:
        return {"status": "at_risk", "confidence": "medium", "evidence": evidence, "reason": None}
    return {"status": "violated", "confidence": "medium", "evidence": evidence, "reason": None}
