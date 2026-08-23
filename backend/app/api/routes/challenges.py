"""Challenge API: browse packs, reveal hints progressively, submit for scoring.

Submissions are graded by the deterministic engine (see app.challenges.scoring)
and stored as an append-only attempt history per client key.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.challenges.scoring import SubmissionError, grade_submission
from app.content import challenge_loader
from app.db import get_db
from app.evaluation import canonical_json
from app.persistence.models import SubmissionRecord, utcnow

router = APIRouter(prefix="/api/challenges", tags=["challenges"])

DbSession = Annotated[Session, Depends(get_db)]


class SubmitBody(BaseModel):
    graph: dict[str, Any]
    architecture_id: str | None = None


def _require(cid: str) -> dict[str, Any]:
    challenge = challenge_loader.get_challenge(cid)
    if challenge is None:
        raise HTTPException(status_code=404, detail=f"challenge '{cid}' not found")
    return challenge


@router.get("")
def list_all() -> list[dict[str, Any]]:
    return challenge_loader.list_challenges()


@router.get("/{cid}")
def detail(cid: str) -> dict[str, Any]:
    challenge = _require(cid)
    doc: dict[str, Any] = {k: v for k, v in challenge.items() if k != "hints"}
    doc["hint_count"] = len(challenge.get("hints") or [])
    if challenge.get("starting_graph_ref"):
        doc["starting_graph"] = challenge_loader.load_starting_graph(
            challenge["starting_graph_ref"]
        )
    return doc


@router.get("/{cid}/hints")
def hints(cid: str, level: int = 1) -> dict[str, Any]:
    """Progressive hint ladder: returns the first ``level`` hints only."""
    challenge = _require(cid)
    ladder = challenge.get("hints") or []
    if level < 1:
        raise HTTPException(status_code=422, detail="level must be >= 1")
    revealed = ladder[:level]
    return {
        "challenge_id": cid,
        "level": min(level, len(ladder)),
        "total": len(ladder),
        "hints": revealed,
    }


@router.post("/{cid}/submit")
def submit(
    cid: str,
    body: SubmitBody,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    challenge = _require(cid)
    try:
        report = grade_submission(challenge, body.graph)
    except SubmissionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    attempt = 1 + (
        db.query(SubmissionRecord)
        .filter(
            SubmissionRecord.owner_key == x_client_key,
            SubmissionRecord.challenge_id == cid,
        )
        .count()
    )
    db.add(
        SubmissionRecord(
            owner_key=x_client_key,
            challenge_id=cid,
            attempt=attempt,
            score=report["score"],
            passed=report["passed"],
            graph_json=_dump(body.graph),
            result_json=_dump(report),
        )
    )
    db.commit()
    return {**report, "attempt": attempt, "evaluated_at": utcnow().isoformat() + "Z"}


@router.get("/{cid}/submissions")
def my_submissions(
    cid: str, db: DbSession, x_client_key: str | None = Header(default=None)
) -> list[dict[str, Any]]:
    rows = (
        db.query(SubmissionRecord)
        .filter(SubmissionRecord.owner_key == x_client_key, SubmissionRecord.challenge_id == cid)
        .order_by(SubmissionRecord.attempt)
        .all()
    )
    return [
        {
            "attempt": r.attempt,
            "score": r.score,
            "passed": r.passed,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
        }
        for r in rows
    ]


def _dump(value: Any) -> str:
    return canonical_json(value)
