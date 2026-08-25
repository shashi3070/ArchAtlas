"""Interview API endpoints.

Provides the interview session lifecycle: start, message, advance, report.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.interview_service import (
    InterviewError,
    advance_phase,
    generate_report,
    get_session,
    process_candidate_message,
    start_interview,
)

router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartInterviewRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    scenario: str = Field(min_length=1, max_length=500)


class CandidateMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    graph: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None


class GenerateReportRequest(BaseModel):
    graph: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None


def _require_session(session_id: str) -> None:
    if get_session(session_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )


@router.post("/start")
async def start_interview_endpoint(req: StartInterviewRequest) -> dict[str, Any]:
    """Start a new interview session with the given scenario."""
    existing = get_session(req.session_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session '{req.session_id}' already exists",
        )
    return start_interview(
        db=None, session_id=req.session_id, scenario=req.scenario
    )


@router.post("/{session_id}/message")
async def send_candidate_message(
    session_id: str, req: CandidateMessageRequest
) -> dict[str, Any]:
    """Send a candidate's message and get the interviewer's response."""
    _require_session(session_id)
    try:
        return process_candidate_message(
            db=None,
            session_id=session_id,
            message=req.message,
            graph=req.graph,
            evaluation=req.evaluation,
        )
    except InterviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None


@router.post("/{session_id}/advance")
async def advance_interview_phase(session_id: str) -> dict[str, Any]:
    """Advance to the next interview phase."""
    _require_session(session_id)
    try:
        return advance_phase(db=None, session_id=session_id)
    except InterviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None


@router.get("/{session_id}")
async def get_interview_session(session_id: str) -> dict[str, Any]:
    """Get the current state of an interview session."""
    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return {
        "session_id": session.session_id,
        "scenario": session.scenario,
        "current_phase": session.current_phase.value,
        "transcript": [t.model_dump() for t in session.transcript],
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    }


@router.post("/{session_id}/report")
async def generate_interview_report(
    session_id: str, req: GenerateReportRequest | None = None
) -> dict[str, Any]:
    """Generate the final interview report."""
    _require_session(session_id)
    try:
        graph = req.graph if req else None
        evaluation = req.evaluation if req else None
        return generate_report(
            db=None,
            session_id=session_id,
            graph=graph,
            evaluation=evaluation,
        )
    except InterviewError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from None
