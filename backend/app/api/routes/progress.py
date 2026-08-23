"""Progress tracking API (anonymous client-key identity until auth phase)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content import topics_loader
from app.db import get_db
from app.persistence.models import ProgressEntry, utcnow

router = APIRouter(prefix="/api/progress", tags=["progress"])

DbSession = Annotated[Session, Depends(get_db)]


def _require_client_key(x_client_key: str | None) -> str:
    if not x_client_key or len(x_client_key) < 8 or len(x_client_key) > 64:
        raise HTTPException(status_code=400, detail="Missing or invalid X-Client-Key header")
    return x_client_key


class ProgressUpdate(BaseModel):
    item_id: str = Field(min_length=1, max_length=160)
    kind: str = Field(pattern="^(topic|section)$")
    completed: bool = True
    quiz_score: float | None = Field(default=None, ge=0.0, le=1.0)


@router.get("")
def get_progress(
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    owner = _require_client_key(x_client_key)
    rows = db.scalars(select(ProgressEntry).where(ProgressEntry.owner_key == owner)).all()
    known_topics = set(topics_loader.load_topics())
    entries = [
        {
            "item_id": r.item_id,
            "kind": r.kind,
            "completed": r.completed,
            "quiz_score": r.quiz_score,
            "updated_at": r.updated_at.isoformat() + "Z",
        }
        for r in rows
        # Drop progress rows for topics that no longer exist in content.
        if r.kind != "topic" or r.item_id.split("#")[0] in known_topics
    ]
    completed_topics = {str(e["item_id"]).split("#")[0] for e in entries if e["completed"]}
    total = len(topics_loader.load_topics())
    return {
        "entries": entries,
        "stats": {
            "topics_completed": len(completed_topics),
            "topics_total": total,
            "completion_pct": round(100 * len(completed_topics) / total, 1) if total else 0.0,
        },
    }


@router.put("")
def upsert_progress(
    update: ProgressUpdate,
    db: DbSession,
    x_client_key: str | None = Header(default=None),
) -> dict[str, Any]:
    owner = _require_client_key(x_client_key)
    if update.kind == "topic" and update.item_id.split("#")[0] not in topics_loader.load_topics():
        raise HTTPException(status_code=404, detail=f"Unknown topic '{update.item_id}'")

    row = db.scalars(
        select(ProgressEntry).where(
            ProgressEntry.owner_key == owner,
            ProgressEntry.item_id == update.item_id,
        )
    ).first()
    if row is None:
        row = ProgressEntry(owner_key=owner, item_id=update.item_id, kind=update.kind)
        db.add(row)
    row.kind = update.kind
    row.completed = update.completed
    if update.quiz_score is not None:
        row.quiz_score = max(update.quiz_score, row.quiz_score or 0.0)
    row.updated_at = utcnow()
    db.flush()
    return {
        "item_id": row.item_id,
        "kind": row.kind,
        "completed": row.completed,
        "quiz_score": row.quiz_score,
    }
