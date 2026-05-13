from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from backend.models import Base

TEST_DB = "sqlite+aiosqlite:///data/test_api.db"


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


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@api.com", "password": "secret123", "display_name": "Test"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["email"] == "test@api.com"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@api.com", "password": "secret123", "display_name": "L"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@api.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_bad_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bad@api.com", "password": "secret123", "display_name": "B"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad@api.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "flow@api.com", "password": "secret123", "display_name": "Flow"},
    )
    token = reg.json()["access_token"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "flow@api.com"


@pytest.mark.asyncio
async def test_create_and_list_personas(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "p@api.com", "password": "secret123", "display_name": "P"},
    )
    token = reg.json()["access_token"]

    r = await client.post(
        "/api/v1/personas",
        json={"name": "My Persona", "bio": "Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201

    r = await client.get(
        "/api/v1/personas", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_create_and_get_project(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "proj@api.com", "password": "secret123", "display_name": "Pr"},
    )
    token = reg.json()["access_token"]

    p = await client.post(
        "/api/v1/personas",
        json={"name": "P"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = p.json()["id"]

    r = await client.post(
        "/api/v1/projects",
        json={"persona_id": pid, "name": "Test Project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    proj_id = r.json()["id"]

    r = await client.get(
        f"/api/v1/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "del@api.com", "password": "secret123", "display_name": "Del"},
    )
    token = reg.json()["access_token"]

    p = await client.post(
        "/api/v1/personas",
        json={"name": "P"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = p.json()["id"]

    r = await client.post(
        "/api/v1/projects",
        json={"persona_id": pid, "name": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    proj_id = r.json()["id"]

    r = await client.delete(
        f"/api/v1/projects/{proj_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    r = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 0
