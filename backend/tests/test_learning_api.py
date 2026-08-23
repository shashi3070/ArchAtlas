"""Contract tests for the learning content + progress APIs (Phase 1)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_topics_list_contract(client: TestClient) -> None:
    res = client.get("/api/topics")
    assert res.status_code == 200
    topics = res.json()
    assert len(topics) >= 10
    first = topics[0]
    for key in ("id", "title", "category", "order", "summary", "section_slugs"):
        assert key in first
    orders = [t["order"] for t in topics]
    assert orders == sorted(orders)


def test_topic_detail_has_sections_and_quiz(client: TestClient) -> None:
    res = client.get("/api/topics/caching")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "caching"
    assert len(body["sections"]) >= 4
    for section in body["sections"]:
        assert section["content_md"]
        assert section["title"]
    quiz = body["quiz"]
    assert len(quiz) >= 2
    for item in quiz:
        assert item["answer"] < len(item["options"])
        assert item["explain"]


def test_unknown_topic_404(client: TestClient) -> None:
    assert client.get("/api/topics/nope").status_code == 404


def test_glossary_sorted(client: TestClient) -> None:
    terms = client.get("/api/glossary").json()
    assert len(terms) >= 20
    names = [t["term"] for t in terms]
    assert names == sorted(names, key=str.lower)


def test_search_finds_sections(client: TestClient) -> None:
    body = client.get("/api/search", params={"q": "stampede"}).json()
    assert body["query"] == "stampede"
    hits = body["results"]
    assert any(h["topic_id"] == "caching" for h in hits)


CLIENT = {"X-Client-Key": "pytest-user-0001"}


def test_progress_roundtrip_and_stats(client: TestClient) -> None:
    put = client.put(
        "/api/progress",
        json={"item_id": "caching", "kind": "topic", "completed": True},
        headers=CLIENT,
    )
    assert put.status_code == 200
    got = client.get("/api/progress", headers=CLIENT).json()
    assert got["stats"]["topics_completed"] == 1
    entry = next(e for e in got["entries"] if e["item_id"] == "caching")
    assert entry["completed"] is True

    # Idempotent second write keeps stats stable.
    client.put(
        "/api/progress",
        json={"item_id": "caching", "kind": "topic", "completed": True},
        headers=CLIENT,
    )
    again = client.get("/api/progress", headers=CLIENT).json()
    assert again["stats"]["topics_completed"] == 1


def test_progress_rejects_unknown_topic_and_bad_key(client: TestClient) -> None:
    bad_key = client.put(
        "/api/progress",
        json={"item_id": "caching", "kind": "topic", "completed": True},
    )
    assert bad_key.status_code == 400
    unknown = client.put(
        "/api/progress",
        json={"item_id": "not-a-topic", "kind": "topic", "completed": True},
        headers=CLIENT,
    )
    assert unknown.status_code == 404
