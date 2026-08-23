"""SQLAlchemy persistence models (P1-P5 scope).

Anonymous identity: clients send an ``X-Client-Key`` UUID header; it becomes
``owner_key``. Real accounts land in the auth phase - every table already
keys ownership by this column so migration is additive.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class ProgressEntry(Base):
    __tablename__ = "progress_entries"
    __table_args__ = (UniqueConstraint("owner_key", "item_id", name="uq_progress_owner_item"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_key: Mapped[str] = mapped_column(String(64), index=True)
    item_id: Mapped[str] = mapped_column(String(128), index=True)  # topic id or topic/section slug
    kind: Mapped[str] = mapped_column(String(32))  # topic | section
    quiz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class SavedArchitecture(Base):
    __tablename__ = "architectures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_key: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    challenge_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    versions: Mapped[list["ArchitectureVersion"]] = relationship(
        back_populates="architecture",
        cascade="all, delete-orphan",
        order_by="ArchitectureVersion.version",
    )


class ArchitectureVersion(Base):
    __tablename__ = "architecture_versions"
    __table_args__ = (UniqueConstraint("architecture_id", "version", name="uq_arch_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    architecture_id: Mapped[str] = mapped_column(
        ForeignKey("architectures.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    graph_json: Mapped[str] = mapped_column(Text)  # canonical architecture graph JSON
    note: Mapped[str] = mapped_column(String(300), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    architecture: Mapped[SavedArchitecture] = relationship(back_populates="versions")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    architecture_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    graph_hash: Mapped[str] = mapped_column(String(64), index=True)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    challenge_id: Mapped[str] = mapped_column(String(128), index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    graph_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class LLMRequestRecord(Base):
    """Usage ledger for every gateway call (PLAN.md section 14)."""

    __tablename__ = "llm_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    task: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(16), default="")
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ResponseCacheRecord(Base):
    __tablename__ = "response_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)  # sha256 of request identity
    task: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
