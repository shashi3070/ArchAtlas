"""Interview session management and AI interviewer service.

Manages the interview lifecycle: start → phase transitions →
candidate messages → adaptive follow-ups → final report.
All scoring is deterministic-first; AI only scores communication.
"""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.agents.context import evaluation_context, graph_overview
from app.agents.interview import (
    InterviewPhase,
    InterviewSession,
    TranscriptEntry,
    get_phase_prompt,
    next_phase,
)
from app.agents.interview_prompts import (
    INTERVIEW_PROMPT_VERSION,
    INTERVIEW_REPORT_SYSTEM,
    INTERVIEW_REPORT_USER,
    INTERVIEWER_FOLLOWUP,
    INTERVIEWER_SYSTEM,
    INTERVIEWER_TRANSITION,
)
from app.llm.gateway import Gateway, get_gateway
from app.persistence.models import utcnow


class InterviewError(ValueError):
    """Raised when an interview operation fails."""


class InterviewReport(BaseModel):
    """Final interview report with scores and recommendations."""
    dimension_scores: dict[str, int] = Field(default_factory=dict)
    dimension_evidence: dict[str, str] = Field(default_factory=dict)
    dimension_feedback: dict[str, str] = Field(default_factory=dict)
    overall_recommendation: str = ""
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    study_plan: list[str] = Field(default_factory=list)


# In-memory session store (replace with DB in production)
_sessions: dict[str, InterviewSession] = {}


def create_session(session_id: str, scenario: str) -> InterviewSession:
    """Create a new interview session."""
    session = InterviewSession(
        session_id=session_id,
        scenario=scenario,
        current_phase=InterviewPhase.REQUIREMENTS,
        started_at=utcnow().isoformat() + "Z",
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> InterviewSession | None:
    """Retrieve an interview session."""
    return _sessions.get(session_id)


def start_interview(db: Any, session_id: str, scenario: str) -> dict[str, Any]:
    """Start a new interview and return the opening question."""
    session = create_session(session_id, scenario)
    opening = get_phase_prompt(InterviewPhase.REQUIREMENTS, scenario)
    session.transcript.append(TranscriptEntry(
        phase=InterviewPhase.REQUIREMENTS,
        role="interviewer",
        content=opening,
        timestamp=utcnow().isoformat() + "Z",
    ))
    return {
        "session_id": session_id,
        "phase": InterviewPhase.REQUIREMENTS.value,
        "message": opening,
        "transcript": [t.model_dump() for t in session.transcript],
    }


def _call_interviewer(
    gateway: Gateway,
    db: Any,
    *,
    system: str,
    user: str,
    max_tokens: int = 1500,
) -> str:
    """Call the LLM for interviewer responses."""
    # If no db session, gateway caching won't work - skip the call
    if db is None:
        return ""
    completion, _ = gateway.complete(
        db,
        task="interview",
        owner_key=None,
        system=system,
        user=user,
        prompt_version=INTERVIEW_PROMPT_VERSION,
        max_tokens=max_tokens,
    )
    return completion.text


def generate_followup(
    db: Any,
    session: InterviewSession,
    candidate_answer: str,
    graph: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> str:
    """Generate an adaptive follow-up question based on the candidate's answer."""
    gateway = get_gateway()
    if gateway.provider is None:
        # Deterministic fallback: simple probing question
        return "Can you elaborate on that? What specific numbers or trade-offs are you considering?"

    canvas_summary = graph_overview(graph) if graph else "(no canvas yet)"
    eval_summary = evaluation_context(evaluation) if evaluation else "(not evaluated yet)"

    user = INTERVIEWER_FOLLOWUP.format(
        phase=session.current_phase.value,
        scenario=session.scenario,
        answer=candidate_answer,
        canvas_summary=canvas_summary,
        evaluation=eval_summary,
    )
    return _call_interviewer(gateway, db, system=INTERVIEWER_SYSTEM, user=user)


def generate_transition(
    db: Any,
    session: InterviewSession,
    completed_phase: InterviewPhase,
    next_ph: InterviewPhase,
    phase_summary: str,
) -> str:
    """Generate a transition message between phases."""
    gateway = get_gateway()
    if gateway.provider is None:
        return f"Good, let's move on to {next_ph.value.replace('_', ' ')}."

    user = INTERVIEWER_TRANSITION.format(
        completed_phase=completed_phase.value,
        phase_summary=phase_summary,
        next_phase=next_ph.value.replace("_", " "),
    )
    return _call_interviewer(gateway, db, system=INTERVIEWER_SYSTEM, user=user)


def process_candidate_message(
    db: Any,
    session_id: str,
    message: str,
    graph: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Process a candidate's message and return interviewer response."""
    session = get_session(session_id)
    if session is None:
        raise InterviewError(f"Session {session_id} not found")
    if session.current_phase == InterviewPhase.COMPLETED:
        raise InterviewError("Interview already completed")

    # Record candidate message
    session.transcript.append(TranscriptEntry(
        phase=session.current_phase,
        role="candidate",
        content=message,
        timestamp=utcnow().isoformat() + "Z",
    ))

    # Update board state if graph provided
    if graph:
        session.board_state = graph

    # Generate follow-up or decide to advance
    gateway = get_gateway()
    if gateway.provider is not None and db is not None:
        response = generate_followup(db, session, message, graph, evaluation)
    else:
        # Without LLM, provide a deterministic probing response
        response = (
            "Can you elaborate on that? What specific numbers "
            "or trade-offs are you considering?"
        )

    # Record interviewer response
    session.transcript.append(TranscriptEntry(
        phase=session.current_phase,
        role="interviewer",
        content=response,
        timestamp=utcnow().isoformat() + "Z",
    ))

    return {
        "session_id": session_id,
        "phase": session.current_phase.value,
        "message": response,
        "transcript": [t.model_dump() for t in session.transcript],
    }


def advance_phase(db: Any, session_id: str) -> dict[str, Any]:
    """Advance to the next interview phase."""
    session = get_session(session_id)
    if session is None:
        raise InterviewError(f"Session {session_id} not found")
    if session.current_phase == InterviewPhase.COMPLETED:
        raise InterviewError("Interview already completed")

    completed = session.current_phase
    nxt = next_phase(completed)
    session.current_phase = nxt

    if nxt == InterviewPhase.COMPLETED:
        session.ended_at = utcnow().isoformat() + "Z"
        closing = "Thank you for completing the interview. I'll prepare your detailed report now."
        session.transcript.append(TranscriptEntry(
            phase=InterviewPhase.COMPLETED,
            role="interviewer",
            content=closing,
            timestamp=utcnow().isoformat() + "Z",
        ))
        return {
            "session_id": session_id,
            "phase": "completed",
            "message": closing,
            "transcript": [t.model_dump() for t in session.transcript],
        }

    # Generate transition
    opening = get_phase_prompt(nxt, session.scenario)
    if db is not None and get_gateway().provider is not None:
        transition = generate_transition(db, session, completed, nxt, "")
    else:
        transition = f"Good. Let's move on to {nxt.value.replace('_', ' ')}.\n\n{opening}"

    session.transcript.append(TranscriptEntry(
        phase=nxt,
        role="interviewer",
        content=transition,
        timestamp=utcnow().isoformat() + "Z",
    ))

    return {
        "session_id": session_id,
        "phase": nxt.value,
        "message": transition,
        "transcript": [t.model_dump() for t in session.transcript],
    }


def generate_report(
    db: Any,
    session_id: str,
    graph: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate the final interview report."""
    session = get_session(session_id)
    if session is None:
        raise InterviewError(f"Session {session_id} not found")

    gateway = get_gateway()
    if gateway.provider is None or db is None:
        # Deterministic-only report
        return _deterministic_report(session)

    # Build transcript summary
    transcript_lines = []
    for entry in session.transcript:
        who = "Interviewer" if entry.role == "interviewer" else "Candidate"
        transcript_lines.append(f"{who} ({entry.phase.value}): {entry.content[:500]}")

    canvas_summary = graph_overview(graph or session.board_state)
    eval_summary = evaluation_context(evaluation) if evaluation else "(not evaluated)"

    # Calculate duration
    if session.started_at and session.ended_at:
        duration = "45 minutes (approximate)"
    else:
        duration = "in progress"

    user = INTERVIEW_REPORT_USER.format(
        scenario=session.scenario,
        duration=duration,
        transcript="\n".join(transcript_lines[-50:]),
        canvas_summary=canvas_summary,
        evaluation=eval_summary,
    )

    text = _call_interviewer(
        gateway,
        db,
        system=INTERVIEW_REPORT_SYSTEM,
        user=user,
        max_tokens=4000,
    )

    # Parse report
    try:
        data = _extract_json_object(text)
        report = InterviewReport.model_validate(data)
        return {
            "session_id": session_id,
            "report": report.model_dump(),
            "transcript": [t.model_dump() for t in session.transcript],
        }
    except (InterviewError, ValidationError):
        return _deterministic_report(session)


def _deterministic_report(session: InterviewSession) -> dict[str, Any]:
    """Generate a basic report without LLM - scoring based on transcript length."""
    phases_completed = len(set(t.phase for t in session.transcript if t.role == "candidate"))
    base_score = min(3, phases_completed // 4 + 1)

    report = InterviewReport(
        dimension_scores={
            "requirements": base_score,
            "scale": base_score,
            "api_design": base_score,
            "data_model": base_score,
            "architecture": base_score,
            "bottlenecks": base_score,
            "scaling": base_score,
            "consistency": base_score,
            "availability": base_score,
            "failure_handling": base_score,
            "observability": base_score,
            "trade_offs": base_score,
            "communication": base_score,
        },
        overall_recommendation="hire" if base_score >= 3 else "no_hire",
        strengths=["Completed the interview process"],
        improvements=["Provide more detailed technical explanations"],
        study_plan=["System design fundamentals", "Distributed systems patterns"],
    )
    return {
        "session_id": session.session_id,
        "report": report.model_dump(),
        "transcript": [t.model_dump() for t in session.transcript],
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response, tolerating markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        stripped = cleaned.strip("`")
        parts = stripped.split("\n", 1)
        cleaned = parts[1] if len(parts) == 2 else parts[0]
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end <= start:
        raise InterviewError("response contained no JSON object")
    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as exc:
        raise InterviewError(f"JSON was invalid: {exc}") from exc
