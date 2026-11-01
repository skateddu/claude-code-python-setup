"""Application factory; run with `uv run uvicorn my_app.main:create_app --factory`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from my_app.api.exceptions import register_exception_handlers
from my_app.api.routes import auth, users
from my_app.config import Settings
from my_app.database import create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    # Schema changes go through Alembic migrations, not create_all() at startup.
    await app.state.engine.dispose()


def create_app(settings: Settings | None = None, engine: AsyncEngine | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings and engine instead of the environment's."""
    settings = settings or Settings()
    engine = engine or create_async_engine(settings.database_url, pool_pre_ping=True)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine=engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(auth.router)
    app.include_router(users.router)
    return app
