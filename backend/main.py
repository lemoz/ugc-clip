"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import load_settings
from backend.models.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = load_settings()
    app.state.settings = settings
    if settings.auto_create_tables:
        await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="UGC Clip",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from backend.api.routes_auth import router as auth_router
    from backend.api.routes_briefs import router as briefs_router
    from backend.api.routes_personas import router as personas_router
    from backend.api.routes_pipeline import router as pipeline_router
    from backend.api.routes_projects import router as projects_router
    from backend.api.routes_uploads import router as uploads_router

    app.include_router(auth_router)
    app.include_router(briefs_router)
    app.include_router(personas_router)
    app.include_router(pipeline_router)
    app.include_router(projects_router)
    app.include_router(uploads_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
