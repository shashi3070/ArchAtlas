"""Interview session state machine and interviewer agent.

Implements the twelve-step method for system design interviews.
The interviewer drives the conversation through phases, consuming
board state (candidate's canvas) and adaptive follow-ups.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InterviewPhase(StrEnum):
    """The 12 interview phases."""
    REQUIREMENTS = "requirements"
    SCALE = "scale"
    API_DESIGN = "api_design"
    DATA_MODEL = "data_model"
    ARCHITECTURE = "architecture"
    BOTTLENECKS = "bottlenecks"
    SCALING = "scaling"
    CONSISTENCY = "consistency"
    AVAILABILITY = "availability"
    FAILURE_HANDLING = "failure_handling"
    OBSERVABILITY = "observability"
    TRADE_OFFS = "trade_offs"
    COMPLETED = "completed"


# Ordered list for traversal
PHASE_ORDER: list[InterviewPhase] = [
    InterviewPhase.REQUIREMENTS,
    InterviewPhase.SCALE,
    InterviewPhase.API_DESIGN,
    InterviewPhase.DATA_MODEL,
    InterviewPhase.ARCHITECTURE,
    InterviewPhase.BOTTLENECKS,
    InterviewPhase.SCALING,
    InterviewPhase.CONSISTENCY,
    InterviewPhase.AVAILABILITY,
    InterviewPhase.FAILURE_HANDLING,
    InterviewPhase.OBSERVABILITY,
    InterviewPhase.TRADE_OFFS,
]


class TranscriptEntry(BaseModel):
    """One message in the interview transcript."""
    phase: InterviewPhase
    role: str = Field(pattern="^(interviewer|candidate)$")
    content: str
    timestamp: str  # ISO 8601


class InterviewSession(BaseModel):
    """Mutable interview state stored in memory (or DB later)."""
    session_id: str
    scenario: str  # e.g. "Design a URL shortener"
    current_phase: InterviewPhase = InterviewPhase.REQUIREMENTS
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    board_state: dict[str, Any] = Field(default_factory=dict)  # candidate's graph
    phase_scores: dict[str, int] = Field(default_factory=dict)  # phase -> 1-5
    phase_feedback: dict[str, str] = Field(default_factory=dict)  # phase -> feedback
    started_at: str = ""  # ISO 8601
    ended_at: str = ""


def next_phase(current: InterviewPhase) -> InterviewPhase:
    """Return the next phase, or COMPLETED if at end."""
    try:
        idx = PHASE_ORDER.index(current)
        if idx + 1 < len(PHASE_ORDER):
            return PHASE_ORDER[idx + 1]
    except ValueError:
        pass
    return InterviewPhase.COMPLETED


def get_phase_prompt(phase: InterviewPhase, scenario: str) -> str:
    """Return the interviewer's opening question for a given phase."""
    prompts = {
        InterviewPhase.REQUIREMENTS: (
            f"Let's start with requirements. You're designing a system for: {scenario}.\n\n"
            "Before we dive in, I'd like you to clarify the requirements:\n"
            "- What are the core functional requirements?\n"
            "- What non-functional requirements matter most "
            "(latency, throughput, availability, consistency)?\n"
            "- Any constraints (budget, team size, timeline)?\n\n"
            "Walk me through your understanding of the problem."
        ),
        InterviewPhase.SCALE: (
            "Good. Now let's talk about scale.\n\n"
            "- How many users do you expect at peak?\n"
            "- What's the expected read/write ratio?\n"
            "- What are the data volumes involved?\n"
            "- Any specific latency targets (p50, p95, p99)?\n\n"
            "Help me understand the numbers we're designing for."
        ),
        InterviewPhase.API_DESIGN: (
            "Let's define the API surface.\n\n"
            "- What endpoints does the system expose?\n"
            "- What are the request/response shapes?\n"
            "- Are there any specific API conventions (REST, GraphQL, gRPC)?\n\n"
            "Walk me through the key APIs."
        ),
        InterviewPhase.DATA_MODEL: (
            "Now let's think about data modeling.\n\n"
            "- What are the main entities/tables?\n"
            "- What are the access patterns?\n"
            "- Any specific consistency requirements for the data model?\n\n"
            "Show me how you'd structure the data."
        ),
        InterviewPhase.ARCHITECTURE: (
            "Time for the high-level architecture.\n\n"
            "- Walk me through the major components and how they connect.\n"
            "- What's the request flow from client to response?\n"
            "- Where does caching fit in?\n\n"
            "Draw out the architecture for me."
        ),
        InterviewPhase.BOTTLENECKS: (
            "Let's identify potential bottlenecks.\n\n"
            "- Where are the chokepoints in your design?\n"
            "- What happens under sudden traffic spikes?\n"
            "- Which components are single points of failure?\n\n"
            "What keeps you up at night about this system?"
        ),
        InterviewPhase.SCALING: (
            "How do we scale this system?\n\n"
            "- What's your horizontal scaling strategy?\n"
            "- How do you handle data partitioning/sharding?\n"
            "- What caching layers would you add?\n\n"
            "Walk me through scaling from 100 to 1 million users."
        ),
        InterviewPhase.CONSISTENCY: (
            "Let's discuss consistency guarantees.\n\n"
            "- What consistency model does each component use?\n"
            "- How do you handle distributed transactions if needed?\n"
            "- What are the consistency vs availability trade-offs?\n\n"
            "Where do you need strong consistency vs eventual?"
        ),
        InterviewPhase.AVAILABILITY: (
            "Let's talk about availability.\n\n"
            "- What's your target availability (99.9%, 99.99%, 99.999%)?\n"
            "- How do you handle regional failures?\n"
            "- What's your disaster recovery strategy?\n\n"
            "How do we keep this system running?"
        ),
        InterviewPhase.FAILURE_HANDLING: (
            "How does the system handle failures?\n\n"
            "- What's your retry strategy?\n"
            "- How do you handle partial failures?\n"
            "- What circuit breakers or bulkheads would you add?\n\n"
            "Walk me through a failure scenario."
        ),
        InterviewPhase.OBSERVABILITY: (
            "Let's cover observability.\n\n"
            "- What metrics would you track?\n"
            "- What does your logging strategy look like?\n"
            "- How do you set up distributed tracing?\n"
            "- What alerts would you configure?\n\n"
            "How do you know when something is wrong?"
        ),
        InterviewPhase.TRADE_OFFS: (
            "Finally, let's discuss trade-offs.\n\n"
            "- What are the top 3 trade-offs in your design?\n"
            "- What would you do differently with more time?\n"
            "- What are the risks you're accepting?\n\n"
            "Summarize your design and its key decisions."
        ),
    }
    return prompts.get(phase, "Please continue.")
