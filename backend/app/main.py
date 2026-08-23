"""FastAPI application factory.

Modular monolith per PLAN.md section 13. Domain/evaluation/simulation packages
must never import from api/, llm/, or persistence/.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import architectures, components, health, progress, topics
from app.content import loader, topics_loader
from app.core.config import get_settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Fail fast at startup if the seeded content violates canonical schemas.
    loader.load_catalog()
    topics_loader.load_topics()
    topics_loader.load_glossary()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(components.router)
    app.include_router(topics.router)
    app.include_router(progress.router)
    app.include_router(architectures.router)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


app = create_app()
