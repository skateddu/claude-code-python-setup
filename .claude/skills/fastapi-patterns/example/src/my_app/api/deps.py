"""Shared dependencies: settings, database session, services, current user."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from my_app.config import Settings
from my_app.models.user import User
from my_app.repositories.user_repository import UserRepository
from my_app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_settings(request: Request) -> Settings:
    """Settings the app was created with, injected rather than imported as a global."""
    return request.app.state.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request; uncommitted work is rolled back when it closes."""
    async with request.app.state.session_factory() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_service(session: SessionDep, settings: SettingsDep) -> UserService:
    return UserService(repository=UserRepository(session=session), settings=settings)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], service: UserServiceDep
) -> User:
    return await service.user_from_token(token)


CurrentUserDep = Annotated[User, Depends(get_current_user)]
