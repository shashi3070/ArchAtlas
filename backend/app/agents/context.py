"""Deterministic context builders: turn engine output and graphs into the
compact evidence blocks the prompts inject. No LLM calls happen here.
"""

from typing import Any


def evaluation_context(result: dict[str, Any]) -> str:
    """Render a run_evaluation result into a stable evidence block."""
    lines: list[str] = []
    summary = result.get("summary") or {}
    lines.append(f"overall={summary.get('overall_status', 'unknown')}")
    if "score" in result:
        lines.append(f"score={result['score']}")

    fails = [
        f for f in result.get("rule_results", []) if f.get("severity") == "fail"
    ]
    warns = [f for f in result.get("rule_results", []) if f.get("severity") == "warning"]

    def _finding(f: dict[str, Any]) -> str:
        bits = [f"- {f.get('rule_id')} [{f.get('severity')}]: {f.get('message')}"]
        for ev in f.get("evidence", []) or []:
            bits.append(f"    evidence: {ev}")
        return "\n".join(bits)

    lines.append("FAIL FINDINGS:")
    lines.extend(_finding(f) for f in fails) if fails else lines.append("(none)")
    lines.append("WARNINGS:")
    lines.extend(_finding(w) for w in warns[:8])
    if len(warns) > 8:
        lines.append(f"(+{len(warns) - 8} more warnings)")

    spofs = result.get("spofs") or []
    lines.append(
        "SPOFS: " + ("; ".join(str(s) for s in spofs[:6]) if spofs else "(none)")
    )
    bottlenecks = result.get("bottlenecks") or []
    lines.append(
        "BOTTLENECKS: "
        + ("; ".join(str(b) for b in bottlenecks[:6]) if bottlenecks else "(none)")
    )

    recs = (result.get("recommendations") or [])[:5]
    if recs:
        lines.append("RECOMMENDATIONS (catalog-backed):")
        for r in recs:
            lines.append(f"- {r}")

    reqs = result.get("requirement_outcomes") or []
    if reqs:
        lines.append("REQUIREMENT OUTCOMES:")
        for o in reqs:
            lines.append(
                f"- {o.get('requirement_id')} [{o.get('status')}]: {o.get('reason', '')}"
            )

    return "\n".join(lines)


def graph_overview(graph: dict[str, Any]) -> str:
    """Compact node/edge listing; safe to embed in prompts."""
    lines: list[str] = ["NODES:"]
    for n in graph.get("nodes", []):
        avail = n.get("availability") or {}
        replicas = avail.get("replicas")
        props = n.get("properties") or {}
        prop_bits = ",".join(sorted(k for k, v in props.items() if v)) or "-"
        lines.append(
            f"- id={n.get('id')} type={n.get('type')} name={n.get('name')!r} "
            f"replicas={replicas if replicas is not None else 1} props={prop_bits}"
        )
    lines.append("EDGES:")
    for e in graph.get("edges", []):
        lines.append(
            f"- {e.get('source')} -> {e.get('target')} "
            f"[{e.get('traffic_type', 'sync_request')}]"
        )
    return "\n".join(lines)


def requirements_block(requirements: list[dict[str, Any]]) -> str:
    if not requirements:
        return "(no explicit requirements)"
    out = []
    for r in requirements:
        target = (
            f" target={r['value']}{r.get('unit') or ''}" if r.get("value") is not None else ""
        )
        out.append(
            f"- [{r.get('priority', 'must')}] {r['id']}: {r['description']}{target}"
        )
    return "\n".join(out)
