"""Job model for background task queue (ported from GOV CLIP)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def _uuid():
    import uuid

    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("projects.id"), nullable=True, index=True
    )
    segment_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("segments.id"), nullable=True, index=True
    )
    persona_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("personas.id"), nullable=True, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    progress: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project | None] = relationship(back_populates="jobs")
    segment: Mapped[Segment | None] = relationship()
