"""Phase 5 tests: gateway (cache/metering/ledger), prompt contracts,
agent endpoints, and proposal parsing."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from app.agents import service
from app.db import get_session_factory
from app.llm import gateway as gw
from app.llm.gateway import Gateway, LLMRateLimited, LLMUnavailable
from app.llm.providers import Completion
from app.persistence.models import LLMRequestRecord


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses: list[str] = []

    def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
        self.calls.append({"system": system, "user": user, "max_tokens": max_tokens})
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
        def complete(self, system: str, user: str, *, max_tokens: int) -> Completion:
            super().complete(system, user, max_tokens=max_tokens)
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
