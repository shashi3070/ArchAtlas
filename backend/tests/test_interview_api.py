"""Interview API contract tests (Phase 6)."""

import uuid


def _unique_id() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def test_start_interview(client) -> None:
    sid = _unique_id()
    resp = client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a URL shortener",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["phase"] == "requirements"
    assert len(data["message"]) > 0
    assert len(data["transcript"]) >= 1


def test_start_interview_duplicate_id(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a chat system",
    })
    resp = client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a chat system",
    })
    assert resp.status_code == 409


def test_get_interview_session(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a notification system",
    })
    resp = client.get(f"/api/interview/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["scenario"] == "Design a notification system"
    assert data["current_phase"] == "requirements"


def test_get_interview_session_not_found(client) -> None:
    resp = client.get("/api/interview/nonexistent-session")
    assert resp.status_code == 404


def test_send_candidate_message(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a payment system",
    })
    resp = client.post(f"/api/interview/{sid}/message", json={
        "message": "The system should handle 1000 transactions per second.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert len(data["message"]) > 0
    # Transcript should have the candidate message + interviewer response
    assert len(data["transcript"]) >= 3


def test_send_message_to_unknown_session(client) -> None:
    resp = client.post("/api/interview/nonexistent/message", json={
        "message": "Hello?",
    })
    assert resp.status_code == 404


def test_advance_interview_phase(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a web crawler",
    })
    resp = client.post(f"/api/interview/{sid}/advance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "scale"


def test_advance_completed_session(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a search system",
    })
    # Advance through all 12 phases
    for _ in range(12):
        client.post(f"/api/interview/{sid}/advance")
    # Try to advance after completion
    resp = client.post(f"/api/interview/{sid}/advance")
    assert resp.status_code == 400


def test_generate_report(client) -> None:
    sid = _unique_id()
    client.post("/api/interview/start", json={
        "session_id": sid,
        "scenario": "Design a ride-sharing service",
    })
    resp = client.post(f"/api/interview/{sid}/report")
    assert resp.status_code == 200
    data = resp.json()
    assert "report" in data
    assert "dimension_scores" in data["report"]
    assert len(data["report"]["dimension_scores"]) >= 10
    assert "overall_recommendation" in data["report"]


def test_report_for_unknown_session(client) -> None:
    resp = client.post("/api/interview/nonexistent/report")
    assert resp.status_code == 404
