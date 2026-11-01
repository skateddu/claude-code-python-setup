"""Business rules for registration, authentication and profile updates."""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from my_app.config import Settings
from my_app.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from my_app.models.user import User
from my_app.repositories.user_repository import UserRepository
from my_app.schemas.user import UserCreate, UserUpdate

PASSWORD_HASH = PasswordHash.recommended()
# Verified when the email is unknown, so a miss takes as long as a wrong password.
DUMMY_PASSWORD_HASH = PASSWORD_HASH.hash("dummy-password-for-timing")


class UserService:
    """User use cases; framework-agnostic and testable without HTTP."""

    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def register(self, payload: UserCreate) -> User:
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=PASSWORD_HASH.hash(payload.password),
        )
        return await self._repository.save(user)

    async def get(self, user_id: int) -> User:
        user = await self._repository.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def list_page(self, offset: int, limit: int) -> tuple[list[User], int]:
        return await self._repository.list_page(offset=offset, limit=limit)

    async def update(self, user_id: int, payload: UserUpdate, acting_user: User) -> User:
        if acting_user.id != user_id:
            raise PermissionDeniedError("Users can only update their own profile")
        user = await self.get(user_id)
        for field_name, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field_name, value)
        return await self._repository.save(user)

    async def authenticate(self, email: str, password: str) -> str:
        """Return an access token for valid credentials."""
        user = await self._repository.get_by_email(email)
        stored_hash = user.hashed_password if user else DUMMY_PASSWORD_HASH
        is_valid_password = PASSWORD_HASH.verify(password, stored_hash)
        if user is None or not is_valid_password:
            raise AuthenticationError("Incorrect email or password")
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self._settings.access_token_expire_minutes
        )
        return jwt.encode(
            {"sub": str(user.id), "exp": expires_at},
            self._settings.jwt_secret_key.get_secret_value(),
            algorithm=self._settings.jwt_algorithm,
        )

    async def user_from_token(self, token: str) -> User:
        """Resolve a bearer token to an active user."""
        try:
            claims = jwt.decode(
                token,
                self._settings.jwt_secret_key.get_secret_value(),
                algorithms=[self._settings.jwt_algorithm],
            )
            user_id = int(claims["sub"])
        except (jwt.InvalidTokenError, KeyError, ValueError) as err:
            raise AuthenticationError("Could not validate credentials") from err
        user = await self._repository.get(user_id)
        if user is None:
            raise AuthenticationError("Could not validate credentials")
        if not user.is_active:
            raise PermissionDeniedError("Inactive user")
        return user
