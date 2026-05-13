"""Asset model for TTS audio, lip sync video, and other artifacts."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def _uuid():
    import uuid

    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("projects.id"), nullable=False, index=True
    )
    segment_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("segments.id"), nullable=True, index=True
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="assets")
    segment: Mapped[Segment | None] = relationship(back_populates="assets")
