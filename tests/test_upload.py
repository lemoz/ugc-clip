from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Persona, SourceClip, User, VoiceProfile
from backend.pipeline.stage import StageContext
from backend.pipeline.stages.stage_0_onboard import OnboardStage
from backend.pipeline.upload import ensure_upload_dir

TEST_DB = "sqlite+aiosqlite:///data/test_upload.db"


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


@pytest.mark.asyncio
async def test_ensure_upload_dir():
    dir_path = ensure_upload_dir("test_category")
    assert dir_path.exists()
    assert "test_category" in str(dir_path)


@pytest.mark.asyncio
async def test_onboard_creates_persona(session: AsyncSession):
    user = User(email="o1@test.com", password_hash="h", display_name="O")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="Test", display_name="Test")
    session.add(persona)
    await session.commit()

    stage = OnboardStage()
    ctx = StageContext(
        session=session,
        project_id="proj_none",
        user_id=user.id,
        persona_id=persona.id,
        data={"persona_name": "Onboard Me"},
    )

    result = await stage.run(ctx)
    assert result.passed
    assert result.output["persona_id"] == persona.id


@pytest.mark.asyncio
async def test_onboard_with_clip_path(session: AsyncSession):
    user = User(email="o2@test.com", password_hash="h", display_name="O")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="Test", display_name="Test")
    session.add(persona)
    await session.commit()

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        clip_path = f.name

    stage = OnboardStage()
    ctx = StageContext(
        session=session,
        project_id="proj_none",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "persona_name": "Test",
            "clip_path": clip_path,
            "source_url": "https://youtube.com/watch?v=test",
        },
    )

    result = await stage.run(ctx)
    assert result.passed
    assert "source_clip_id" in result.output

    result_db = await session.execute(
        select(SourceClip).where(SourceClip.persona_id == persona.id)
    )
    clips = result_db.scalars().all()
    assert len(clips) == 1
    assert clips[0].source_url == "https://youtube.com/watch?v=test"

    Path(clip_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_onboard_with_voice_path(session: AsyncSession):
    user = User(email="o3@test.com", password_hash="h", display_name="O")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="Test", display_name="Test")
    session.add(persona)
    await session.commit()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"fake wav content")
        voice_path = f.name

    stage = OnboardStage()
    ctx = StageContext(
        session=session,
        project_id="proj_none",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "persona_name": "Test",
            "voice_path": voice_path,
            "voice_text": "Hello, this is my voice sample.",
        },
    )

    result = await stage.run(ctx)
    assert result.passed
    assert "voice_profile_id" in result.output

    result_db = await session.execute(
        select(VoiceProfile).where(VoiceProfile.persona_id == persona.id)
    )
    profiles = result_db.scalars().all()
    assert len(profiles) == 1
    assert profiles[0].prompt_text == "Hello, this is my voice sample."

    Path(voice_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_onboard_with_both_clip_and_voice(session: AsyncSession):
    user = User(email="o4@test.com", password_hash="h", display_name="O")
    session.add(user)
    await session.flush()

    persona = Persona(user_id=user.id, name="Test", display_name="Test")
    session.add(persona)
    await session.commit()

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video")
        clip_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"fake wav")
        voice_path = f.name

    stage = OnboardStage()
    ctx = StageContext(
        session=session,
        project_id="proj_none",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "persona_name": "Test",
            "clip_path": clip_path,
            "voice_path": voice_path,
        },
    )

    result = await stage.run(ctx)
    assert result.passed
    assert "source_clip_id" in result.output
    assert "voice_profile_id" in result.output

    Path(clip_path).unlink(missing_ok=True)
    Path(voice_path).unlink(missing_ok=True)
