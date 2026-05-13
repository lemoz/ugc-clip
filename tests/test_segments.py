from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models import Base, Persona, User
from backend.pipeline.lipsync.service import StubLipsyncService
from backend.pipeline.stage import StageContext
from backend.pipeline.stages.stage_5_segments import SegmentGenerationStage
from backend.pipeline.stages.stage_6_audio import AudioMixStage
from backend.pipeline.tts.service import StubTtsService

TEST_DB = "sqlite+aiosqlite:///data/test_segments.db"


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


async def _setup(session: AsyncSession):
    user = User(email="seg@test.com", password_hash="h", display_name="S")
    session.add(user)
    await session.flush()
    persona = Persona(user_id=user.id, name="SP", display_name="SP")
    session.add(persona)
    await session.commit()
    return user, persona


@pytest.mark.asyncio
async def test_tts_stub_generates_file():
    service = StubTtsService()
    result = await service.generate(
        script_text="Hello world. This is a test.",
        voice_prompt_audio="/tmp/nonexistent.wav",
    )
    assert Path(result.audio_path).exists()
    assert result.duration_seconds > 0


@pytest.mark.asyncio
async def test_lipsync_stub_copies_file():
    service = StubLipsyncService()

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video")
        src = f.name

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await service.generate(video_path=src, audio_path=src, output_dir=tmpdir)
        assert Path(result.video_path).exists()

    Path(src).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_segment_generation_stage(session: AsyncSession):
    user, persona = await _setup(session)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video data")
        clip_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVE")
        voice_path = f.name

    ctx = StageContext(
        session=session,
        project_id="proj_seg",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "script": {
                    "text": "This is a test script for the segment generation stage.",
                },
                "shot_plan": {
                    "segments": [
                        {"segment_index": 0, "shot_type": "close-up"},
                        {"segment_index": 1, "shot_type": "medium"},
                    ],
                },
                "source_clip_id": "clip_test",
                "voice_profile": {
                    "prompt_audio_path": voice_path,
                    "prompt_text": "Test voice prompt",
                },
            },
        },
    )

    stage = SegmentGenerationStage(
        tts_service=StubTtsService(),
        lipsync_service=StubLipsyncService(),
    )
    result = await stage.run(ctx)
    assert result.passed
    assert len(result.output["segments"]) == 2
    assert result.output["segments"][0]["status"] == "complete"
    assert result.output["segments"][1]["status"] == "complete"

    Path(clip_path).unlink(missing_ok=True)
    Path(voice_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_audio_mix_stage(session: AsyncSession):
    user, persona = await _setup(session)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(b"RIFF\x24\x00\x00\x00WAVE")
        tts_path = f.name

    ctx = StageContext(
        session=session,
        project_id="proj_audio",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "segments": [
                    {
                        "segment_index": 0,
                        "tts_path": tts_path,
                        "status": "complete",
                    },
                    {
                        "segment_index": 1,
                        "tts_path": tts_path,
                        "status": "complete",
                    },
                ],
            },
        },
    )

    stage = AudioMixStage()
    result = await stage.run(ctx)
    assert result.passed
    assert result.output["segment_count"] == 2
    assert result.output["normalized"] is True

    Path(tts_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_audio_mix_stage_no_segments(session: AsyncSession):
    user, persona = await _setup(session)

    ctx = StageContext(
        session=session,
        project_id="proj_audio2",
        user_id=user.id,
        persona_id=persona.id,
        data={
            "previous_stage_output": {
                "segments": [],
            },
        },
    )

    stage = AudioMixStage()
    result = await stage.run(ctx)
    assert not result.passed
    assert len(result.errors) > 0
