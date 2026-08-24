"""Phase 5 tests: gateway (cache/metering/ledger), prompt contracts,
agent endpoints, and proposal parsing."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.agents import service
from app.db import get_session_factory
from app.llm import gateway as gw
from app.llm.gateway import Gateway, LLMRateLimited, LLMUnavailable
from app.llm.providers import Completion, OpenAICompatProvider
from app.persistence.models import LLMRequestRecord


@dataclass
class FakeProvider:
    name: str = "fake"
    model: str = "fake-model"
    # Mutable state lives in init fields (not __post_init__) so that
    # dataclasses.replace(model=...) keeps sharing lists with the fixture.
    calls: list[dict[str, Any]] = field(default_factory=list)
    responses: list[str] = field(default_factory=list)

    def complete(
        self, system: str, user: str, *, max_tokens: int, json_mode: bool = False
    ) -> Completion:
        self.calls.append(
            {
                "system": system,
                "user": user,
                "max_tokens": max_tokens,
                "json_mode": json_mode,
                "model": self.model,
            }
        )
        text = self.responses.pop(0) if self.responses else "ok"
        return Completion(text=text, tokens_in=11, tokens_out=7)


@pytest.fixture()
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeProvider:
    provider = FakeProvider()
    monkeypatch.setattr(gw, "_gateway", Gateway(provider=provider, daily_limit=5))
    return provider


@pytest.fixture()
def no_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gw, "_gateway", Gateway(provider=None))


@contextmanager
def _db() -> Iterator[Any]:
    db = get_session_factory()()
    try:
        yield db
        db.commit()
    finally:
        db.close()


# ---------- gateway units ----------


def test_gateway_caches_and_ledgers(fake: FakeProvider) -> None:
    with _db() as db:
        first, hit1 = gw.get_gateway().complete(
            db, task="explain", owner_key="k1", system="s", user="u", prompt_version="v1"
        )
        second, hit2 = gw.get_gateway().complete(
            db, task="explain", owner_key="k1", system="s", user="u", prompt_version="v1"
        )
        assert not hit1 and hit2
        assert first.text == second.text == "ok"
        assert len(fake.calls) == 1  # second call served from cache
        rows = db.query(LLMRequestRecord).filter(LLMRequestRecord.owner_key == "k1").all()
        assert len(rows) == 2
        assert sorted(r.cache_hit for r in rows) == [False, True]


def test_gateway_meters_completed_calls_per_day(fake: FakeProvider) -> None:
    monkey_gateway = Gateway(provider=fake, daily_limit=1)
    with _db() as db:
        monkey_gateway.complete(db, task="t", owner_key="metered", system="s", user="a")
        with pytest.raises(LLMRateLimited):
            monkey_gateway.complete(db, task="t", owner_key="metered", system="s", user="b")


def test_cache_hits_do_not_consume_quota(fake: FakeProvider) -> None:
    monkey_gateway = Gateway(provider=fake, daily_limit=1)
    with _db() as db:
        _, miss = monkey_gateway.complete(
            db, task="t", owner_key="q", system="s", user="same"
        )
        assert not miss
        # Quota is now exhausted; the identical request must still be served
        # from the cache rather than rejected.
        _, hit = monkey_gateway.complete(
            db, task="t", owner_key="q", system="s", user="same"
        )
    assert hit


def test_no_provider_raises_unavailable(no_provider: None) -> None:
    with _db() as db, pytest.raises(LLMUnavailable):
        gw.get_gateway().complete(db, task="t", owner_key="x", system="s", user="u")


def test_failed_calls_are_ledgered_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom(FakeProvider):
        def complete(
            self, system: str, user: str, *, max_tokens: int, json_mode: bool = False
        ) -> Completion:
            super().complete(system, user, max_tokens=max_tokens, json_mode=json_mode)
            raise gw.LLMProviderError("upstream exploded")

    boom = Boom()
    monkeypatch.setattr(gw, "_gateway", Gateway(provider=boom, daily_limit=5))
    with _db() as db:
        with pytest.raises(gw.LLMProviderError):
            gw.get_gateway().complete(db, task="t", owner_key="err", system="s", user="u")
        row = (
            db.query(LLMRequestRecord).filter(LLMRequestRecord.owner_key == "err").one()
        )
        assert row.error is not None and "upstream exploded" in row.error


# ---------- prompt contracts ----------


def test_critique_prompt_contains_fail_findings_verbatim(fake: FakeProvider) -> None:
    result = {
        "summary": {"overall_status": "fail"},
        "score": 41.0,
        "rule_results": [
            {
                "rule_id": "ha.single_database",
                "severity": "fail",
                "message": "single database node",
            }
        ],
        "spofs": [],
        "bottlenecks": [],
    }
    graph = {"nodes": [], "edges": []}
    with _db() as db:
        service.critique_graph(db, "k", result, graph)
    sent = fake.calls[0]
    assert "ha.single_database" in sent["user"]
    assert "treat these as facts" in sent["user"]
    assert sent["system"] == service.MENTOR_SYSTEM


def test_proposal_prompt_demands_strict_json(fake: FakeProvider) -> None:
    result = {"summary": {"overall_status": "fail"}, "rule_results": []}
    fake.responses.append('{"summary": "", "add_nodes": [], "connect": []}')
    with _db() as db:
        service.propose_diff(db, "k", result, {"nodes": [], "edges": []}, "add caching")
    assert '"add_nodes"' in fake.calls[0]["user"]


# ---------- proposal parsing ----------


def test_parse_proposal_tolerates_fences() -> None:
    raw = (
        "```json\n"
        + json.dumps(
            {
                "summary": "add a cache",
                "add_nodes": [
                    {"ref": "c1", "component_type": "redis", "name": "Cache", "replicas": 1}
                ],
                "connect": [{"source_ref": "api-1", "target_ref": "c1"}],
                "set_properties": [
                    {"match_component_type": "postgresql", "availability": {"replicas": 2}}
                ],
                "remove_node_ids": [],
            }
        )
        + "\n```"
    )
    proposal = service.parse_proposal(raw)
    assert proposal.add_nodes[0].component_type == "redis"
    assert proposal.connect[0].traffic_type == "sync_request"


def test_parse_proposal_rejects_garbage() -> None:
    with pytest.raises(service.AgentError):
        service.parse_proposal("I would add a cache somewhere, probably.")


def test_parse_proposal_rejects_wrong_shape() -> None:
    with pytest.raises(service.AgentError):
        service.parse_proposal(json.dumps({"add_nodes": "just add redis"}))


# ---------- API endpoints ----------


def test_explain_deterministic_when_no_provider(
    client: Any, no_provider: None
) -> None:
    res = client.post(
        "/api/agent/explain",
        json={"result": {"summary": {"overall_status": "fail"}, "rule_results": []}},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "deterministic"
    assert "Overall status" in body["text"]


def test_explain_via_llm(client: Any, fake: FakeProvider) -> None:
    fake.responses.append("Your design fails because the database is a SPOF.")
    res = client.post(
        "/api/agent/explain",
        json={
            "result": {
                "summary": {"overall_status": "fail"},
                "rule_results": [
                    {"rule_id": "ha.spof", "severity": "fail", "message": "spof"}
                ],
            }
        },
        headers={"X-Client-Key": "explain-k"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "llm" and "SPOF" in body["text"]


def test_critique_503_without_provider(client: Any, no_provider: None) -> None:
    res = client.post("/api/agent/critique", json={"graph": {"nodes": [], "edges": []}})
    assert res.status_code == 503


def test_hint_404_unknown_challenge(client: Any, fake: FakeProvider) -> None:
    res = client.post("/api/agent/challenges/nope/hint?level=1")
    assert res.status_code == 404


def test_hint_via_llm(client: Any, fake: FakeProvider) -> None:
    fake.responses.append("Think about what happens when one AZ disappears.")
    res = client.post(
        "/api/agent/challenges/us-3-survive-az-loss/hint?level=1",
        headers={"X-Client-Key": "hint-k"},
    )
    assert res.status_code == 200
    assert res.json()["text"].startswith("Think about")


def test_proposal_endpoint_roundtrip(client: Any, fake: FakeProvider) -> None:
    fake.responses.append(
        json.dumps(
            {
                "summary": "scale the database tier",
                "add_nodes": [],
                "connect": [],
                "set_properties": [
                    {
                        "match_component_type": "postgresql",
                        "properties": {},
                        "availability": {"replicas": 2},
                    }
                ],
                "remove_node_ids": [],
            }
        )
    )
    res = client.post(
        "/api/agent/proposal",
        json={"graph": {"nodes": [], "edges": []}, "goal": "survive db loss"},
        headers={"X-Client-Key": "prop-k"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["proposal"]["set_properties"][0]["availability"]["replicas"] == 2


def test_proposal_invalid_json_maps_to_422(client: Any, fake: FakeProvider) -> None:
    fake.responses.append("Sorry, I cannot help with that.")
    res = client.post(
        "/api/agent/proposal",
        json={"graph": {"nodes": [], "edges": []}, "goal": ""},
    )
    assert res.status_code == 422


def test_daily_limit_maps_to_429(client: Any) -> None:
    provider = FakeProvider()
    monkey_gateway = Gateway(provider=provider, daily_limit=0)
    original = gw._gateway
    gw._gateway = monkey_gateway
    try:
        res = client.post(
            "/api/agent/explain",
            json={"result": {"summary": {}, "rule_results": []}},
            headers={"X-Client-Key": "limited"},
        )
    finally:
        gw._gateway = original
    assert res.status_code == 429


# ---------- provider failure -> 502, providers matrix, chat endpoint ----------

def _graph_payload() -> dict[str, Any]:
    from tests.eval_helpers import CLIENT_LB_API_DB
    return CLIENT_LB_API_DB


def test_provider_failure_maps_to_502(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        name = "boom"
        model = "boom-1"

        def complete(
            self, system: str, user: str, *, max_tokens: int, json_mode: bool = False
        ) -> Completion:
            raise gw.LLMProviderError("HTTP 401: invalid api key")

    monkeypatch.setattr(gw, "_gateway", Gateway(provider=Boom(), daily_limit=5))
    res = client.post("/api/agent/critique", json={"graph": _graph_payload()})
    assert res.status_code == 502
    assert "HTTP 401" in res.json()["detail"]


def test_providers_matrix_shape(client: Any) -> None:
    res = client.get("/api/agent/providers")
    assert res.status_code == 200
    body = res.json()
    ids = [p["id"] for p in body["providers"]]
    assert {"openai", "groq", "anthropic", "gemini", "ollama"} <= set(ids)
    for p in body["providers"]:
        assert isinstance(p["key_present"], bool)
        assert "api_key" not in json.dumps(p), "key material must never leak"
        # Azure is the one provider with no usable default model - it needs
        # an explicit SDP_LLM_MODEL deployment name.
        if p["id"] != "azure":
            assert p["default_model"]


def test_chat_roundtrip_returns_reply_and_fix(client: Any, fake: FakeProvider) -> None:
    fake.responses.append(json.dumps(
        {
            "reply": "Add a cache in front of the API.",
            "suggest": ["Why redis?", "What about TTLs?", "How big should it be?"],
            "fix": {
                "summary": "add redis",
                "add_nodes": [
                    {"ref": "c1", "component_type": "redis_cache", "name": "session-cache"}
                ],
                "connect": [
                    {"source_ref": "c1", "target_ref": "api", "traffic_type": "sync_request"}
                ],
                "set_properties": [],
                "remove_node_ids": [],
            },
        }
    ))
    res = client.post(
        "/api/agent/chat",
        json={
            "graph": _graph_payload(),
            "messages": [
                {"role": "user", "content": "what should I add first?"},
                {"role": "assistant", "content": "start with the data layer"},
                {"role": "user", "content": "how do I cut latency?"},
            ],
            "goal": "cut latency",
        },
        headers={"X-Client-Key": "chat-1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["reply"].startswith("Add a cache")
    assert body["suggest"] == ["Why redis?", "What about TTLs?", "How big should it be?"]
    assert body["fix"]["add_nodes"][0]["component_type"] == "redis_cache"
    sent = fake.calls[0]
    assert "start with the data layer" in sent["user"], "history must reach the prompt"
    assert "cut latency" in sent["user"]
    assert sent["system"].startswith("You are")


def test_chat_degrades_gracefully_on_non_json(client: Any, fake: FakeProvider) -> None:
    fake.responses.append("Honestly, your design looks solid - just add replicas to the API.")
    res = client.post(
        "/api/agent/chat",
        json={"graph": _graph_payload(), "messages": [{"role": "user", "content": "thoughts?"}]},
    )
    assert res.status_code == 200
    body = res.json()
    assert "solid" in body["reply"]
    assert body["fix"]["add_nodes"] == []
    assert len(body["suggest"]) == 3, "fallback suggestions must exist"


def test_chat_empty_messages_422(client: Any, fake: FakeProvider) -> None:
    res = client.post("/api/agent/chat", json={"graph": _graph_payload(), "messages": []})
    assert res.status_code == 422


def test_chat_rate_limited_maps_to_429(
    client: Any, fake: FakeProvider, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gw, "_gateway", Gateway(provider=fake, daily_limit=0))
    res = client.post(
        "/api/agent/chat",
        json={"graph": _graph_payload(), "messages": [{"role": "user", "content": "hi"}]},
    )
    assert res.status_code == 429
    assert "Retry-After" in res.headers


# ---------- model overrides + live model listing ----------

def test_model_override_and_json_mode_reach_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, bool]] = []

    @dataclass
    class Recording:
        name: str = "rec"
        model: str = "base-model"

        def complete(
            self, system: str, user: str, *, max_tokens: int, json_mode: bool = False
        ) -> Completion:
            seen.append((self.model, json_mode))
            return Completion(text="ok", tokens_in=1, tokens_out=1)

    monkeypatch.setattr(gw, "_gateway", Gateway(provider=Recording(), daily_limit=5))
    with _db() as db:
        gw._gateway.complete(  # type: ignore[union-attr]
            db,
            task="chat",
            owner_key="u",
            system="s",
            user="q",
            model_override="custom-x",
            json_mode=True,
        )
    assert seen == [("custom-x", True)]


def test_chat_endpoint_sends_json_mode_and_model(client: Any, fake: FakeProvider) -> None:
    fake.responses.append(json.dumps({"reply": "r", "fix": {}}))
    res = client.post(
        "/api/agent/chat",
        json={
            "graph": _graph_payload(),
            "messages": [{"role": "user", "content": "hi"}],
            "model": "openai/gpt-oss-20b",
        },
    )
    assert res.status_code == 200
    call = fake.calls[0]
    assert call["json_mode"] is True
    assert call["model"] == "openai/gpt-oss-20b"


class _FakeResp:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict[str, Any]:
        return self._payload


def test_list_provider_models_filters_non_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gw,
        "build_named_provider",
        lambda pid: OpenAICompatProvider(
            name="groq", base_url="http://x/v1", api_key="k", model="m"
        ),
    )
    monkeypatch.setattr(
        gw,
        "_models_http_get",
        lambda url, headers, timeout: _FakeResp(
            {
                "data": [
                    {"id": "whisper-large-v3"},
                    {"id": "meta-llama/llama-prompt-guard-2-86m"},
                    {"id": "canopylabs/orpheus-v1-english"},
                    {"id": "openai/gpt-oss-120b"},
                    {"id": "groq/compound"},
                ]
            }
        ),
    )
    gw._MODEL_CACHE.clear()
    models = gw.list_provider_models("groq")
    assert models == ["groq/compound", "openai/gpt-oss-120b"]


def test_models_endpoint_success_and_error(client: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gw, "list_provider_models", lambda pid: ["m-a", "m-b"])
    ok = client.get("/api/agent/models?provider=groq")
    assert ok.status_code == 200
    body = ok.json()
    assert body["models"] == ["m-a", "m-b"]
    assert body["default_model"] == "openai/gpt-oss-120b"

    def _boom(pid: str) -> list[str]:
        raise LLMUnavailable("no API key available for Anthropic Claude")

    monkeypatch.setattr(gw, "list_provider_models", _boom)
    bad = client.get("/api/agent/models?provider=anthropic")
    assert bad.status_code == 200
    assert bad.json()["models"] == []
    assert "no API key" in bad.json()["error"]

    missing = client.get("/api/agent/models")
    assert missing.status_code == 422

