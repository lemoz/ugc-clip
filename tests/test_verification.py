from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Persona, User
from backend.verification.persona import NoopVerifier, PersonaVerifier
from backend.verification.provider import (
    VerificationResult,
    handle_webhook_event,
    start_verification,
)

TEST_DB = "sqlite+aiosqlite:///data/test_verify.db"


@pytest.fixture
async def engine():
    engine = create_async_engine(TEST_DB, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def _create_persona(session: AsyncSession) -> Persona:
    user = User(email="v@test.com", password_hash="h", display_name="V")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="VP", display_name="VP")
    session.add(persona)
    await session.commit()
    return persona


@pytest.mark.asyncio
async def test_verification_result():
    result = VerificationResult(verified=True, provider="test", inquiry_id="inq_1")
    assert result.verified
    assert result.provider == "test"


@pytest.mark.asyncio
async def test_noop_verifier():
    verifier = NoopVerifier()
    result = await verifier.create_session(Persona(user_id="x", name="T", display_name="T"))
    assert result.verified
    assert result.provider == "noop"


@pytest.mark.asyncio
async def test_persona_verifier_no_key():
    verifier = PersonaVerifier(api_key="", template_id=None)
    persona = Persona(user_id="x", name="T", display_name="T")
    result = await verifier.create_session(persona)
    assert not result.verified
    assert "PERSONA_API_KEY" in (result.errors or [""])[0]


@pytest.mark.asyncio
async def test_start_verification_with_noop(session: AsyncSession):
    persona = await _create_persona(session)
    verifier = NoopVerifier()

    result = await start_verification(session, persona.id, verifier)
    assert "verification_id" in result
    assert result["verified"] is True

    await session.refresh(persona)
    assert persona.verification_status == "pending"


@pytest.mark.asyncio
async def test_handle_webhook_with_noop(session: AsyncSession):
    persona = await _create_persona(session)
    verifier = NoopVerifier()

    await start_verification(session, persona.id, verifier)

    webhook_result = await handle_webhook_event(session, verifier, {"event": "check.completed"})
    assert webhook_result["verified"] is True
