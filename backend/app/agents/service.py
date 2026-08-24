"""Agent service: prompt assembly + gateway calls for each AI task.

Every task is grounded in deterministic engine evidence. The explain task
degrades to a fully deterministic summary when no provider is configured
(deterministic-first/AI-second); all other tasks surface 503 loudly.
"""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.agents.context import (
    evaluation_context,
    graph_overview,
    requirements_block,
)
from app.agents.prompts import (
    CHAT_SYSTEM,
    CHAT_USER,
    CRITIQUE_USER,
    EXPLAIN_USER,
    HINT_USER,
    MENTOR_SYSTEM,
    PROMPT_VERSION,
    PROPOSAL_USER,
)
from app.llm.gateway import Gateway, get_gateway
from app.persistence.models import utcnow


class AgentError(ValueError):
    """Raised when an agent response cannot be parsed into a proposal."""


class ProposalAddNode(BaseModel):
    ref: str = Field(min_length=1, max_length=64)
    component_type: str = Field(min_length=1, max_length=64)
    name: str | None = None
    replicas: int = Field(default=1, ge=1, le=100)


class ProposalConnect(BaseModel):
    source_ref: str = Field(min_length=1, max_length=64)
    target_ref: str = Field(min_length=1, max_length=64)
    traffic_type: str = Field(default="sync_request")


class ProposalSetProperties(BaseModel):
    match_component_type: str = Field(min_length=1, max_length=64)
    properties: dict[str, Any] = Field(default_factory=dict)
    availability: dict[str, Any] = Field(default_factory=dict)


class GraphDiffProposal(BaseModel):
    """Proposal-only edit plan; nothing applies without explicit user approval
    in the UI (the backend never mutates graphs from proposals)."""

    summary: str = ""
    add_nodes: list[ProposalAddNode] = Field(default_factory=list)
    connect: list[ProposalConnect] = Field(default_factory=list)
    set_properties: list[ProposalSetProperties] = Field(default_factory=list)
    remove_node_ids: list[str] = Field(default_factory=list)


def _call(
    gateway: Gateway,
    db: Any,
    *,
    task: str,
    owner_key: str | None,
    user: str,
    max_tokens: int,
    system: str = MENTOR_SYSTEM,
    provider_id: str = "",
    model_override: str = "",
    json_mode: bool = False,
) -> tuple[str, bool]:
    completion, cache_hit = gateway.complete(
        db,
        task=task,
        owner_key=owner_key,
        system=system,
        user=user,
        prompt_version=PROMPT_VERSION,
        max_tokens=max_tokens,
        provider_id=provider_id,
        model_override=model_override,
        json_mode=json_mode,
    )
    return completion.text, cache_hit


def _fail_findings(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in result.get("rule_results", []) if f.get("severity") == "fail"]


def deterministic_explain(result: dict[str, Any]) -> str:
    """No-provider fallback: a readable summary built purely from evidence."""
    summary = result.get("summary") or {}
    lines: list[str] = [
        f"Overall status: {summary.get('overall_status', 'unknown')}."
    ]
    if "score" in result:
        lines.append(f"Weighted score: {result['score']}%.")
    fails = _fail_findings(result)
    if fails:
        lines.append("Blocking findings:")
        lines.extend(f"- {f.get('rule_id')}: {f.get('message')}" for f in fails)
    spofs = result.get("spofs") or []
    if spofs:
        lines.append(f"Single points of failure: {len(spofs)}")
    bottlenecks = result.get("bottlenecks") or []
    for b in bottlenecks[:3]:
        node = b.get("node_id") or b.get("node")
        if node:
            lines.append(f"Bottleneck at {node}: {b.get('detail', '')}".rstrip(": "))
    recs = (result.get("recommendations") or [])[:3]
    if recs:
        lines.append("Suggested next steps:")
        lines.extend(f"- {r}" for r in recs)
    return "\n".join(lines)


def explain_result(
    db: Any, owner_key: str | None, result: dict[str, Any]
) -> dict[str, Any]:
    gateway = get_gateway()
    if gateway.provider is None:
        return {
            "task": "explain",
            "source": "deterministic",
            "text": deterministic_explain(result),
            "cache_hit": False,
            "generated_at": utcnow().isoformat() + "Z",
        }
    text, cache_hit = _call(
        gateway,
        db,
        task="explain",
        owner_key=owner_key,
        user=EXPLAIN_USER.format(evidence=evaluation_context(result)),
        max_tokens=1500,
    )
    return {
        "task": "explain",
        "source": "llm",
        "text": text,
        "cache_hit": cache_hit,
        "generated_at": utcnow().isoformat() + "Z",
    }


def critique_graph(
    db: Any, owner_key: str | None, result: dict[str, Any], graph: dict[str, Any]
) -> dict[str, Any]:
    summary = result.get("summary") or {}
    warns = [f for f in result.get("rule_results", []) if f.get("severity") == "warning"]
    user = CRITIQUE_USER.format(
        overall=summary.get("overall_status", "unknown"),
        score=result.get("score", "n/a"),
        fail_findings=(
            "\n".join(f"- {f['rule_id']}: {f['message']}" for f in _fail_findings(result))
            or "(none)"
        ),
        warnings="\n".join(f"- {w['rule_id']}: {w['message']}" for w in warns) or "(none)",
        spofs=json.dumps(result.get("spofs") or []),
        bottlenecks=json.dumps(result.get("bottlenecks") or []),
        overview=graph_overview(graph),
    )
    text, cache_hit = _call(
        get_gateway(),
        db,
        task="critique",
        owner_key=owner_key,
        user=user,
        max_tokens=2200,
    )
    return {"task": "critique", "source": "llm", "text": text, "cache_hit": cache_hit}


def challenge_hint(
    db: Any,
    owner_key: str | None,
    challenge: dict[str, Any],
    level: int,
    revealed: list[str],
    graph: dict[str, Any] | None,
) -> dict[str, Any]:
    ladder = challenge.get("hints") or []
    user = HINT_USER.format(
        challenge_id=challenge["id"],
        difficulty=challenge.get("difficulty", "?"),
        mode=challenge.get("mode", "challenge"),
        level=level,
        total=len(ladder) or level,
        requirements=requirements_block(challenge.get("requirements") or []),
        overview=graph_overview(graph) if graph else "(nothing drawn yet)",
        revealed="\n".join(f"- {h}" for h in revealed) or "(none)",
    )
    text, cache_hit = _call(
        get_gateway(),
        db,
        task="hint",
        owner_key=owner_key,
        user=user,
        max_tokens=600,
    )
    return {"task": "hint", "source": "llm", "text": text, "cache_hit": cache_hit}


def propose_diff(
    db: Any, owner_key: str | None, result: dict[str, Any], graph: dict[str, Any], goal: str
) -> dict[str, Any]:
    user = PROPOSAL_USER.format(
        goal=goal or "address the failing findings",
        evidence=evaluation_context(result),
        overview=graph_overview(graph),
    )
    text, cache_hit = _call(
        get_gateway(),
        db,
        task="proposal",
        owner_key=owner_key,
        user=user,
        max_tokens=2600,
        json_mode=True,
    )
    return {
        "task": "proposal",
        "proposal": parse_proposal(text),
        "raw": text,
        "cache_hit": cache_hit,
    }


def parse_proposal(text: str) -> GraphDiffProposal:
    """Parse the model's JSON (tolerating markdown fences) into a validated
    proposal. Anything unparseable raises AgentError - never guess."""
    data = _extract_json_object(text)
    try:
        return GraphDiffProposal.model_validate(data)
    except ValidationError as exc:
        raise AgentError(f"proposal did not match schema: {exc.error_count()} error(s)") from exc


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


class ChatReply(BaseModel):
    """Strict chat contract: conversational answer + optional machine-usable
    fix so the canvas can render recommended changes, plus clickable
    follow-up suggestions for the learner."""

    reply: str = ""
    suggest: list[str] = Field(default_factory=list)
    fix: GraphDiffProposal = Field(default_factory=GraphDiffProposal)


def _clean_suggestions(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw[:4]:
        text = str(item).strip()[:120]
        if text:
            out.append(text)
    return out


_FALLBACK_SUGGESTIONS = [
    "Explain the FAIL findings in simple terms",
    "How do I remove the single points of failure?",
    "Propose one concrete improvement to this design",
]


def _extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        stripped = cleaned.strip("`")
        parts = stripped.split("\n", 1)
        cleaned = parts[1] if len(parts) == 2 else parts[0]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise AgentError("response contained no JSON object")
    try:
        data: dict[str, Any] = json.loads(cleaned[start : end + 1])
        return data
    except json.JSONDecodeError as exc:
        raise AgentError(f"JSON was invalid: {exc}") from exc


def chat(
    db: Any,
    owner_key: str | None,
    *,
    result: dict[str, Any],
    graph: dict[str, Any],
    messages: list[dict[str, Any]],
    goal: str = "",
    provider_id: str = "",
    model_override: str = "",
) -> dict[str, Any]:
    """Full-context mentor chat: canvas graph + fresh evaluation evidence go
    in; a strict {reply, fix} JSON comes out. The fix is proposal-only."""
    history_lines: list[str] = []
    for m in messages[:-1][-8:]:
        who = "learner" if m.get("role") == "user" else "mentor"
        history_lines.append(f"{who}: {str(m.get('content', ''))[:500]}")
    latest = messages[-1]["content"] if messages else ""

    user = CHAT_USER.format(
        evidence=evaluation_context(result),
        overview=graph_overview(graph),
        goal_line=f"LEARNER GOAL: {goal}" if goal else "",
        history="\n".join(history_lines) or "(new conversation)",
        message=latest,
    )
    text, cache_hit = _call(
        get_gateway(),
        db,
        task="chat",
        owner_key=owner_key,
        system=CHAT_SYSTEM,
        user=user,
        max_tokens=3200,
        provider_id=provider_id,
        model_override=model_override,
        json_mode=True,
    )
    data: dict[str, Any] | None = None
    try:
        data = _extract_json_object(text)
    except AgentError:
        data = None
    parsed: ChatReply | None = None
    if data is not None:
        try:
            parsed = ChatReply.model_validate(data)
        except ValidationError:
            parsed = None
    if parsed is None:
        # Conversational graceful degradation: a mentor answer that is not
        # strict JSON still reaches the learner; only machine-usable fixes
        # require the schema. Empty responses remain an error.
        reply_text = text.strip()
        if not reply_text:
            raise AgentError("model returned an empty chat reply")
        return {
            "task": "chat",
            "reply": reply_text,
            "suggest": list(_FALLBACK_SUGGESTIONS),
            "fix": GraphDiffProposal().model_dump(),
            "raw": text,
            "cache_hit": cache_hit,
        }
    return {
        "task": "chat",
        "reply": parsed.reply,
        "suggest": _clean_suggestions(parsed.suggest) or list(_FALLBACK_SUGGESTIONS),
        "fix": parsed.fix.model_dump(),
        "raw": text,
        "cache_hit": cache_hit,
    }
