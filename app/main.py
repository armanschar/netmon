"""FastAPI application entry point.

Run with: uvicorn app.main:app --reload
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import Settings, load_settings
from app.database import Database

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    A factory (instead of a bare module-level app) lets tests pass their own
    Settings, e.g. a temporary SQLite file, without touching environment variables.
    """
    settings = settings or load_settings()
    database = Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting %s (database=%s)", settings.app_name, settings.database_url)
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.database = database
    app.include_router(health_router)
    return app


app = create_app()
