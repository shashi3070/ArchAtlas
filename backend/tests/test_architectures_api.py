"""Architectures API contract tests: CRUD, immutability, restore semantics."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

HEADERS = {"X-Client-Key": "pytest-arch-user"}


def _graph(node_id: str = "n1", edge_to: str | None = None) -> dict:
    nodes = [
        {"id": node_id, "type": "client", "name": "Web Client",
         "position": {"x": 0, "y": 0}, "properties": {}},
    ]
    if edge_to:
        nodes.append(
            {"id": edge_to, "type": "api", "name": "API",
             "position": {"x": 200, "y": 0},
             "availability": {"replicas": 2, "multi_az": True}, "properties": {}}
        )
    edges = (
        [
            {"id": "e1", "source": node_id, "target": edge_to,
             "traffic_type": "sync_request"}
        ]
        if edge_to
        else []
    )
    return {"id": "arch-test", "version": 1, "nodes": nodes, "edges": edges}


def test_create_get_roundtrip(client: TestClient) -> None:
    res = client.post(
        "/api/architectures",
        json={"name": "My Design", "graph": _graph("a", "b")},
        headers=HEADERS,
    )
    assert res.status_code == 200, res.text
    meta = res.json()
    arch_id = meta["id"]
    assert meta["current_version"] == 1

    got = client.get(f"/api/architectures/{arch_id}", headers=HEADERS).json()
    # Defaults were normalized in.
    edge = got["graph"]["edges"][0]
    assert edge["direction"] == "unidirectional"
    assert got["graph"]["nodes"][1]["availability"]["replicas"] == 2


def test_invalid_graph_rejected_422(client: TestClient) -> None:
    bad = _graph("a", None)
    bad["nodes"][0]["type"] = "Not A Valid Type!"
    res = client.post(
        "/api/architectures", json={"name": "bad", "graph": bad}, headers=HEADERS
    )
    assert res.status_code == 422
    assert "ArchitectureGraph" in res.json()["detail"] or "not valid" in res.json()["detail"]


def test_versions_append_only_and_restore(client: TestClient) -> None:
    arch_id = client.post(
        "/api/architectures",
        json={"name": "Versioned", "graph": _graph("v1")},
        headers=HEADERS,
    ).json()["id"]

    g2 = _graph("v2")
    client.put(f"/api/architectures/{arch_id}", json={"graph": g2, "note": "second"},
               headers=HEADERS)

    versions = client.get(f"/api/architectures/{arch_id}/versions", headers=HEADERS).json()
    assert [v["version"] for v in versions] == [1, 2]
    assert versions[-1]["is_current"] is True

    # Historical version still readable byte-for-byte.
    old = client.post(f"/api/architectures/{arch_id}/versions/1", headers=HEADERS).json()
    assert old["graph"]["nodes"][0]["id"] == "v1"

    # Restore v1 -> appends v3 (immutability: no rows mutated).
    meta = client.post(
        f"/api/architectures/{arch_id}/restore", json={"version": 1}, headers=HEADERS
    ).json()
    assert meta["current_version"] == 3

    restored = client.get(f"/api/architectures/{arch_id}", headers=HEADERS).json()
    assert restored["graph"]["nodes"][0]["id"] == "v1"
    assert restored["graph"]["version"] == 3

    versions = client.get(f"/api/architectures/{arch_id}/versions", headers=HEADERS).json()
    assert [v["version"] for v in versions] == [1, 2, 3]
    notes = {v["version"]: v["note"] for v in versions}
    assert notes[2] == "second"
    assert "restored from v1" in notes[3]


def test_export_attachment(client: TestClient) -> None:
    arch_id = client.post(
        "/api/architectures",
        json={"name": "Exported", "graph": _graph("x")},
        headers=HEADERS,
    ).json()["id"]
    res = client.get(f"/api/architectures/{arch_id}/export", headers=HEADERS)
    assert res.status_code == 200
    assert "attachment" in res.headers["content-disposition"]
    body = json.loads(res.content)
    assert body["nodes"][0]["id"] == "x"


def test_owner_isolation(client: TestClient) -> None:
    arch_id = client.post(
        "/api/architectures",
        json={"name": "Private", "graph": _graph("p")},
        headers=HEADERS,
    ).json()["id"]
    other = {"X-Client-Key": "pytest-other-user"}
    assert client.get(f"/api/architectures/{arch_id}", headers=other).status_code == 404
