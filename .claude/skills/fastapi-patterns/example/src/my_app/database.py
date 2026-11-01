"""Declarative base and session factory for async SQLAlchemy."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for every ORM model."""


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build the session factory; attributes stay loaded after commit for async use."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)
