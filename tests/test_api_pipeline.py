from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from backend.models import Base

TEST_DB = "sqlite+aiosqlite:///data/test_api_pipeline.db"


@pytest.fixture(autouse=True)
def set_test_db():
    os.environ["UGC_DATABASE_URL"] = TEST_DB
    os.environ["UGC_SECRET_KEY"] = "test-secret-key-123"
    yield
    os.environ.pop("UGC_DATABASE_URL", None)
    os.environ.pop("UGC_SECRET_KEY", None)


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
async def client(engine) -> AsyncClient:
    from backend.config import load_settings
    from backend.models import base as models_base

    load_settings.cache_clear()
    models_base._engine = None
    models_base._session_factory = None

    from backend.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        yield cl


async def _register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "secret123", "display_name": "Tester"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_fake_generation_pipeline_end_to_end(client: AsyncClient):
    token = await _register(client, "pipeline@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    persona_response = await client.post(
        "/api/v1/personas",
        json={"name": "Pipeline Persona"},
        headers=headers,
    )
    assert persona_response.status_code == 201
    persona_id = persona_response.json()["id"]

    video_response = await client.post(
        "/api/v1/uploads/video",
        data={"persona_id": persona_id},
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
        headers=headers,
    )
    assert video_response.status_code == 201
    source_clip_id = video_response.json()["id"]

    voice_response = await client.post(
        "/api/v1/uploads/voice",
        data={"persona_id": persona_id, "prompt_text": "This is my voice prompt."},
        files={"file": ("voice.wav", b"RIFF$\x00\x00\x00WAVE", "audio/wav")},
        headers=headers,
    )
    assert voice_response.status_code == 201

    brief_response = await client.post(
        "/api/v1/briefs",
        json={
            "template_slug": "product-review",
            "title": "Pipeline Brief",
            "product_name": "Widget",
            "call_to_action": "Try Widget today",
            "tone": "casual",
            "target_duration": 30,
        },
        headers=headers,
    )
    assert brief_response.status_code == 201
    brief_id = brief_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={
            "persona_id": persona_id,
            "brief_id": brief_id,
            "source_clip_id": source_clip_id,
            "name": "Pipeline Project",
        },
        headers=headers,
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    run_response = await client.post(
        f"/api/v1/projects/{project_id}/run",
        json={"template_slug": "product-review", "start_stage": 0, "stop_stage": 9},
        headers=headers,
    )
    assert run_response.status_code == 200
    run_data = run_response.json()
    assert run_data["status"] == "awaiting_review"
    assert run_data["stage"] == 9
    assert len(run_data["results"]) == 10
    assert all(result["status"] == "passed" for result in run_data["results"])

    artifacts_response = await client.get(
        f"/api/v1/projects/{project_id}/artifacts", headers=headers
    )
    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) == 10
    assert artifacts[-1]["content"]["output"]["download_url"].endswith("/download")

    download_response = await client.get(f"/api/v1/projects/{project_id}/download", headers=headers)
    assert download_response.status_code == 200
    assert download_response.content.startswith(b"ugc-clip-fake-video")


@pytest.mark.asyncio
async def test_project_rejects_other_users_brief(client: AsyncClient):
    user_a = await _register(client, "owner@example.com")
    user_b = await _register(client, "attacker@example.com")

    owner_headers = {"Authorization": f"Bearer {user_a}"}
    attacker_headers = {"Authorization": f"Bearer {user_b}"}

    brief_response = await client.post(
        "/api/v1/briefs",
        json={"title": "Owner Brief", "product_name": "Widget"},
        headers=owner_headers,
    )
    assert brief_response.status_code == 201
    brief_id = brief_response.json()["id"]

    persona_response = await client.post(
        "/api/v1/personas",
        json={"name": "Attacker Persona"},
        headers=attacker_headers,
    )
    assert persona_response.status_code == 201
    persona_id = persona_response.json()["id"]

    project_response = await client.post(
        "/api/v1/projects",
        json={"persona_id": persona_id, "brief_id": brief_id, "name": "Bad Project"},
        headers=attacker_headers,
    )
    assert project_response.status_code == 404
