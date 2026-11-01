"""Data access for users."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from my_app.exceptions import ConflictError
from my_app.models.user import User


class UserRepository:
    """Queries and writes for `User`; translates database errors into domain errors."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_page(self, offset: int, limit: int) -> tuple[list[User], int]:
        total = await self._session.scalar(select(func.count()).select_from(User))
        # A stable order keeps offset pagination from skipping or repeating rows.
        result = await self._session.scalars(
            select(User).order_by(User.id).offset(offset).limit(limit)
        )
        return list(result), total or 0

    async def save(self, user: User) -> User:
        """Insert or update `user` and commit; a uniqueness violation becomes ConflictError."""
        self._session.add(user)
        try:
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            raise ConflictError("A user with this email or username already exists") from err
        await self._session.refresh(user)
        return user
