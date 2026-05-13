"""Evaluation result model for quality gate assessment."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def _uuid():
    import uuid

    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("projects.id"), nullable=False, index=True
    )
    segment_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("segments.id"), nullable=True, index=True
    )
    evaluator_model: Mapped[str] = mapped_column(String(255), default="qwen3.5-plus")
    stage: Mapped[str] = mapped_column(String(50), default="post_generation")
    lip_sync_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    voice_match: Mapped[str | None] = mapped_column(String(50), nullable=True)
    visual_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    temporal_coherence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    overall_realism: Mapped[str | None] = mapped_column(String(50), nullable=True)
    caption_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cta_present: Mapped[bool | None] = mapped_column(nullable=True)
    audio_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    passed: Mapped[bool] = mapped_column(default=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    critical_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fix_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    project: Mapped[Project] = relationship(back_populates="evaluations")
