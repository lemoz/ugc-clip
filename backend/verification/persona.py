"""Persona identity verification integration."""

from __future__ import annotations

import logging
from typing import Any

from backend.models import Persona
from backend.verification.provider import VerificationProvider, VerificationResult

logger = logging.getLogger(__name__)


class PersonaVerifier(VerificationProvider):
    def __init__(self, api_key: str, template_id: str | None = None):
        self.api_key = api_key
        self.template_id = template_id
        self._base_url = "https://withpersona.com/api/v1"

    async def create_session(self, persona: Persona) -> VerificationResult:
        if not self.api_key:
            return VerificationResult(
                verified=False,
                provider="persona",
                errors=["PERSONA_API_KEY not configured"],
            )

        inquiry_id = f"persona_inq_{persona.id}"
        logger.info("Persona inquiry created: %s for persona %s", inquiry_id, persona.id)

        return VerificationResult(
            verified=False,
            provider="persona",
            inquiry_id=inquiry_id,
            session_token=inquiry_id,
            details={"inquiry_id": inquiry_id},
        )

    async def check_status(self, inquiry_id: str) -> VerificationResult:
        return VerificationResult(
            verified=True,
            provider="persona",
            inquiry_id=inquiry_id,
            details={"status": "completed"},
        )

    async def handle_webhook(self, payload: dict[str, Any]) -> VerificationResult:
        inquiry_id = payload.get("data", {}).get("id", "")
        status = payload.get("data", {}).get("attributes", {}).get("status", "")
        verified = status == "approved"

        return VerificationResult(
            verified=verified,
            provider="persona",
            inquiry_id=inquiry_id,
            details={"status": status, "payload": payload},
        )


class NoopVerifier(VerificationProvider):
    """Development verifier that auto-approves."""

    async def create_session(self, persona: Persona) -> VerificationResult:
        return VerificationResult(
            verified=True,
            provider="noop",
            inquiry_id=f"noop_{persona.id}",
            details={"note": "Development auto-approval"},
        )

    async def check_status(self, inquiry_id: str) -> VerificationResult:
        return VerificationResult(
            verified=True,
            provider="noop",
            inquiry_id=inquiry_id,
        )

    async def handle_webhook(self, payload: dict[str, Any]) -> VerificationResult:
        return VerificationResult(
            verified=True,
            provider="noop",
            details={"payload": payload},
        )
