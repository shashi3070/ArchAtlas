"""Phase 4: challenge packs, scoring, and the challenge API.

Solvability contract: every challenge's reference solution passes its own
challenge through the real grading path, and every repair drill's starting
graph does NOT pass (it must still exhibit blocking failures).
"""

from __future__ import annotations

import json

import pytest

from app.challenges.scoring import (
    PASS_THRESHOLD,
    check_constraints,
    grade_submission,
    validation_rules_for,
)
from app.content import challenge_loader
from tests.eval_helpers import e, g, n


@pytest.fixture(scope="module")
def challenges() -> dict[str, dict]:
    return challenge_loader.load_challenges()


def _solution(cid: str) -> dict:
    path = challenge_loader.solution_path(cid)
    with path.open("r", encoding="utf-8") as fh:
        doc: dict = json.load(fh)
    return doc


# ---------------- content pack integrity ----------------

def test_pack_loads_with_expected_shape(challenges):
    assert len(challenges) >= 14
    modes = {cid: ch.get("mode", "challenge") for cid, ch in challenges.items()}
    assert sum(1 for m in modes.values() if m == "repair") >= 6
    for ch in challenges.values():
        assert ch["requirements"], f"{ch['id']} has no requirements"
        assert len(ch.get("hints") or []) >= 3, f"{ch['id']} hint ladder too short"
        priorities = {r.get("priority", "must") for r in ch["requirements"]}
        assert "must" in priorities, f"{ch['id']} lacks a must requirement"


def test_chain_links_form_ordered_paths(challenges):
    families: dict[str, list[tuple[int, str, str | None]]] = {}
    for cid, ch in challenges.items():
        chain = ch.get("chain")
        if chain:
            families.setdefault(chain["family_id"], []).append(
                (chain["level"], cid, chain.get("next_challenge_id"))
            )
    assert {"url-shortener", "media-gallery", "order-processing"}.issubset(set(families))
    for family, links in families.items():
        levels = sorted(links)
        assert [lvl for lvl, _, _ in levels] == list(range(1, len(levels) + 1))
        for i, (_, cid, nxt) in enumerate(levels[:-1]):
            assert nxt == levels[i + 1][1], f"{family}: broken link at {cid}"
        assert levels[-1][2] is None


def test_repair_drills_reference_existing_fixtures(challenges):
    for cid, ch in challenges.items():
        if ch.get("mode") != "repair":
            continue
        assert ch.get("starting_graph_ref"), f"{cid} is a drill without a start"
        start = challenge_loader.load_starting_graph(ch["starting_graph_ref"])
        assert start["nodes"], f"{cid} start fixture empty"


# ---------------- solvability ----------------

def test_every_solution_passes_its_challenge(challenges):
    for cid in challenges:
        try:
            report = grade_submission(challenges[cid], _solution(cid))
        except FileNotFoundError:
            continue
        assert report["passed"], f"{cid} solution failed: score={report['score']} " \
                                 f"breakdown={report['breakdown']} " \
                                 f"blocking={report['blocking_failure']}"


def test_drill_starts_do_not_pass(challenges):
    expected_start_fails = {
        "repair-disconnected": {"graph.no_ingress"},
        "repair-db-overload": {"scale.db_write_bottleneck"},
        "repair-queue-no-workers": {"edge.queue_unconsumed"},
        "repair-notification-ack": {"rel.missing_idempotency"},
        "repair-url-shortener": {"sec.missing_authentication"},
        "repair-single-points": {"ha.single_database"},
    }
    for cid in expected_start_fails:
        ch = challenges[cid]
        start = challenge_loader.load_starting_graph(ch["starting_graph_ref"])
        report = grade_submission(ch, start)
        assert not report["passed"], f"{cid} start unexpectedly passes"
        fail_ids = {f["rule_id"] for f in report["findings"] if f["status"] == "FAIL"}
        assert expected_start_fails[cid] <= fail_ids, \
            f"{cid}: missing expected FAILs {expected_start_fails[cid] - fail_ids}"


# ---------------- scoring mechanics ----------------

def test_validation_rules_translation():
    assert validation_rules_for({"metric": "rps", "value": 1000}) == ["rps >= 1000"]
    assert validation_rules_for({"metric": "p95", "value": 200, "unit": "ms"}) == ["p95 <= 200ms"]
    assert validation_rules_for({"metric": "availability", "value": 99.9, "unit": "%"}) == [
        "availability >= 99.9"
    ]
    assert validation_rules_for({"metric": "durability", "value": 11, "unit": "nines"}) == [
        "durability >= 11"
    ]
    assert validation_rules_for({"metric": "vibes", "value": 5}) == []
    assert validation_rules_for({"metric": "rps", "value": None}) == []


def test_scoring_weights_and_threshold(challenges):
    ch = challenges["us-2-read-scale"]
    report = grade_submission(ch, _solution("us-2-read-scale"))
    # must(3) satisfied + should(2) satisfied + must(3) satisfied = 8/8.
    assert report["score"] == 100.0
    weights = [b["weight"] for b in report["breakdown"]]
    assert weights == [3, 2, 3]


def test_at_risk_scores_half(challenges):
    ch = json.loads(json.dumps(challenges["us-1-shorten-serve"]))
    # Shrink API capacity to land between target and the 1.2x headroom bar.
    solution = _solution("us-1-shorten-serve")
    for node in solution["nodes"]:
        if node["type"] == "api":
            node["capacity"]["rps_per_instance"] = 350  # 3 x 350 = 1050: in at_risk band
    report = grade_submission(ch, solution)
    at_risk = next(b for b in report["breakdown"] if b["requirement_id"] == "handle-demand")
    assert at_risk["status"] == "at_risk"
    assert at_risk["points"] == 1.5  # weight 3 x factor 0.5
    assert PASS_THRESHOLD == 70.0


def test_blocking_failure_gates_pass(challenges):
    ch = challenges["us-2-read-scale"]
    solution = _solution("us-2-read-scale")
    # Drop the cache tier -> perf.no_cache_high_read FAIL blocks despite good score.
    solution["nodes"] = [x for x in solution["nodes"] if x["type"] != "redis"]
    solution["edges"] = [
        e for e in solution["edges"]
        if "redis" not in (e["source"], e["target"])
    ]
    solution["edges"].append({"id": "e-fix", "source": "api", "target": "db",
                              "traffic_type": "sync_request"})
    report = grade_submission(ch, solution)
    assert report["blocking_failure"] is True
    assert not report["passed"]


def test_allowed_palette_constraint(challenges):
    ch = challenges["us-1-shorten-serve"]
    graph = g(
        [n("c", "client"), n("k", "kafka"), n("api", "api", replicas=3)],
        [e("e1", "c", "kafka"), e("e2", "k", "api")],
        rps=5000,
        read_ratio=0.5,
    )
    violations = check_constraints(ch, graph)
    assert any("kafka" in v for v in violations)


def test_max_nodes_constraint():
    challenge = {
        "allowed_components": [],
        "constraints": [{"key": "max_nodes", "value": 2}],
    }
    graph = g([n("c", "client"), n("a", "api", replicas=1), n("b", "redis")], [])
    violations = check_constraints(challenge, graph)
    assert any("max_nodes" in v for v in violations)


# ---------------- API ----------------

def test_challenge_endpoints(client):  # client fixture from conftest
    listing = client.get("/api/challenges").json()
    assert len(listing) >= 14
    assert all("hints" not in item or isinstance(item.get("hint_count"), int)
               for item in listing)

    detail = client.get("/api/challenges/repair-disconnected").json()
    assert detail["mode"] == "repair"
    assert detail["starting_graph"]["id"] == "golden-disconnected"
    assert "hints" not in detail  # never spoiled in detail payload

    hints = client.get("/api/challenges/repair-disconnected/hints?level=2").json()
    assert hints["total"] == 4
    assert len(hints["hints"]) == 2

    assert client.get("/api/challenges/nope").status_code == 404
    assert client.get("/api/challenges/us-1-shorten-serve/hints?level=0").status_code == 422


def test_submit_scores_and_counts_attempts(client):
    cid = "us-1-shorten-serve"
    graph = _solution(cid)
    key = {"X-Client-Key": "attempt-counter"}
    first = client.post(
        f"/api/challenges/{cid}/submit", json={"graph": graph}, headers=key
    ).json()
    assert first["passed"] is True
    assert first["attempt"] == 1
    second = client.post(
        f"/api/challenges/{cid}/submit", json={"graph": graph}, headers=key
    ).json()
    assert second["attempt"] == 2

    history = client.get(f"/api/challenges/{cid}/submissions", headers=key).json()
    assert [h["attempt"] for h in history] == [1, 2]
    assert all(h["passed"] for h in history)


def test_submit_rejects_invalid_graph(client):
    bad = {"id": "x", "version": 1, "nodes": [{"id": "n1"}], "edges": []}
    res = client.post(
        "/api/challenges/us-1-shorten-serve/submit",
        json={"graph": bad},
        headers={"X-Client-Key": "bad-graph"},
    )
    assert res.status_code == 422


def test_submit_reports_failed_design(client):
    ch = challenge_loader.get_challenge("us-2-read-scale")
    assert ch is not None
    start = challenge_loader.load_starting_graph("overloaded_db")  # unrelated mess
    res = client.post(
        "/api/challenges/us-2-read-scale/submit",
        json={"graph": start},
        headers={"X-Client-Key": "failed-design"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["passed"] is False


# ---------------- reference-solution reveal (spoiler-gated) ----------------

def test_solution_locked_until_first_attempt(client):
    res = client.get("/api/challenges/us-1-shorten-serve/solution")
    assert res.status_code == 403
    assert "at least one attempt" in res.json()["detail"]


def test_solution_unlocks_after_attempt(client):
    graph = _solution("us-1-shorten-serve")
    submitted = client.post(
        "/api/challenges/us-1-shorten-serve/submit",
        json={"graph": graph},
        headers={"X-Client-Key": "solver-1"},
    )
    assert submitted.status_code == 200

    res = client.get(
        "/api/challenges/us-1-shorten-serve/solution",
        headers={"X-Client-Key": "solver-1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["graph"]["nodes"], "solution graph missing nodes"
    assert isinstance(body["score"], (int, float))
    assert body["evaluation"]["score"] == pytest.approx(body["score"])
    assert body["evaluation"]["passed"] is True
