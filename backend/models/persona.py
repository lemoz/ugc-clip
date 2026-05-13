"""Persona, identity verification, voice profile, and source clip models."""
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


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(TEXT, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), default="unverified"
    )
    avatar_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    user: Mapped[User] = relationship(back_populates="personas")
    voice_profile: Mapped[VoiceProfile | None] = relationship(
        back_populates="persona", uselist=False, cascade="all, delete-orphan"
    )
    source_clips: Mapped[list[SourceClip]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )
    identity_verifications: Mapped[list[IdentityVerification]] = relationship(
        back_populates="persona", cascade="all, delete-orphan"
    )
    projects: Mapped[list[Project]] = relationship(back_populates="persona")


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    persona_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("personas.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), default="persona")
    provider_inquiry_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    persona: Mapped[Persona] = relationship(back_populates="identity_verifications")


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    persona_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("personas.id"), nullable=False, unique=True, index=True
    )
    prompt_audio_path: Mapped[str] = mapped_column(String(500), nullable=False)
    prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_duration: Mapped[float] = mapped_column(Float, default=0)
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="extracted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    persona: Mapped[Persona] = relationship(back_populates="voice_profile")


class SourceClip(Base):
    __tablename__ = "source_clips"

    id: Mapped[str] = mapped_column(TEXT, primary_key=True, default=_uuid)
    persona_id: Mapped[str] = mapped_column(
        TEXT, ForeignKey("personas.id"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="upload")
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), default="video")
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    framing_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lighting_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_visibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    is_selected: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    persona: Mapped[Persona] = relationship(back_populates="source_clips")
