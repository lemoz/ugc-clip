"""Identity verification provider system."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import IdentityVerification, Persona


@dataclass
class VerificationResult:
    verified: bool
    provider: str
    inquiry_id: str | None = None
    session_token: str | None = None
    details: dict[str, Any] | None = None
    errors: list[str] | None = None


class VerificationProvider(ABC):
    @abstractmethod
    async def create_session(self, persona: Persona) -> VerificationResult:
        ...

    @abstractmethod
    async def check_status(self, inquiry_id: str) -> VerificationResult:
        ...

    @abstractmethod
    async def handle_webhook(self, payload: dict[str, Any]) -> VerificationResult:
        ...


async def start_verification(
    session: AsyncSession,
    persona_id: str,
    provider: VerificationProvider,
) -> dict[str, Any]:
    result = await session.execute(select(Persona).where(Persona.id == persona_id))
    persona = result.scalar_one_or_none()
    if not persona:
        return {"error": "Persona not found"}

    ver_result = await provider.create_session(persona)

    verification = IdentityVerification(
        persona_id=persona_id,
        provider=ver_result.provider,
        provider_inquiry_id=ver_result.inquiry_id,
        provider_session_id=ver_result.session_token,
        status="in_progress" if ver_result.verified else "pending",
        result=json.dumps(ver_result.details) if ver_result.details else None,
    )
    session.add(verification)

    persona.verification_status = "pending"
    await session.commit()

    return {
        "verification_id": verification.id,
        "session_token": ver_result.session_token,
        "verified": ver_result.verified,
    }


async def handle_webhook_event(
    session: AsyncSession,
    provider: VerificationProvider,
    payload: dict[str, Any],
) -> dict[str, Any]:
    ver_result = await provider.handle_webhook(payload)

    if ver_result.inquiry_id:
        result = await session.execute(
            select(IdentityVerification).where(
                IdentityVerification.provider_inquiry_id == ver_result.inquiry_id
            )
        )
        verification = result.scalar_one_or_none()
        if verification:
            verification.status = "completed" if ver_result.verified else "failed"
            verification.result = (
                json.dumps(ver_result.details) if ver_result.details else None
            )
            verification.completed_at = datetime.now(UTC)

            persona_result = await session.execute(
                select(Persona).where(Persona.id == verification.persona_id)
            )
            persona = persona_result.scalar_one_or_none()
            if persona:
                persona.verification_status = (
                    "verified" if ver_result.verified else "failed"
                )

        await session.commit()

    return {"verified": ver_result.verified}
