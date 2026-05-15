"""Project, brief, template, and segment models."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def _uuid():
    import uuid

    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), default="general")
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(TEXT, ForeignKey("users.id"), nullable=False, index=True)
    template_id: Mapped[str | None] = mapped_column(TEXT, ForeignKey("templates.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    key_claims: Mapped[str | None] = mapped_column(Text, nullable=True)
    call_to_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(100), default="casual")
    target_platform: Mapped[str] = mapped_column(String(50), default="tiktok")
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_duration: Mapped[int] = mapped_column(Integer, default=30)
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    template: Mapped[Template | None] = relationship()
    projects: Mapped[list[Project]] = relationship(back_populates="brief")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(TEXT, ForeignKey("users.id"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("personas.id"), nullable=False, index=True
    )
    brief_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("briefs.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), default="Untitled")
    source_clip_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("source_clips.id"), nullable=True
    )
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    platform: Mapped[str] = mapped_column(String(50), default="tiktok")
    aspect_ratio: Mapped[str] = mapped_column(String(20), default="9:16")
    total_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    stage: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship(back_populates="projects")
    persona: Mapped[Persona] = relationship(back_populates="projects")
    brief: Mapped[Brief | None] = relationship(back_populates="projects")
    source_clip: Mapped[SourceClip | None] = relationship()
    segments: Mapped[list[Segment]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Segment.segment_index"
    )
    assets: Mapped[list[Asset]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    jobs: Mapped[list[Job]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list[EvaluationResult]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    pipeline_artifacts: Mapped[list[PipelineArtifact]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("projects.id"), nullable=False, index=True
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_clip_id: Mapped[str | None] = mapped_column(
        TEXT, ForeignKey("source_clips.id"), nullable=True
    )
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_word_index: Mapped[int] = mapped_column(Integer, default=0)
    end_word_index: Mapped[int] = mapped_column(Integer, default=0)
    duration_estimate: Mapped[float] = mapped_column(Float, default=10.0)
    tts_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lipsync_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    project: Mapped[Project] = relationship(back_populates="segments")
    source_clip: Mapped[SourceClip | None] = relationship()
    assets: Mapped[list[Asset]] = relationship(
        back_populates="segment", cascade="all, delete-orphan"
    )
