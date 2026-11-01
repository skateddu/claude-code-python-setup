---
name: fastapi-patterns
description: FastAPI patterns for this template's stack — src layout with routes, services and repositories, pydantic-settings injected rather than imported, Pydantic v2 schemas, async SQLAlchemy 2.0, domain exceptions mapped to HTTP in one place, OAuth2 with PyJWT and pwdlib, and httpx + pytest-asyncio tests. Use when building or reviewing a FastAPI app — endpoints, schemas, dependencies, auth, error handling or API tests.
metadata:
  origin: ECC (adapted)
---

# FastAPI Patterns

A small but complete user API that follows `.claude/rules/` (`architecture.md`, `api-patterns.md`, `exception-handling.md`, `project-structure.md`, `security.md`, `testing.md`). Every block below is taken from `example/`, a runnable project next to this file whose tests pass on Python 3.10 and 3.12 with warnings as errors (`cd example && uv run pytest`). Read the files there for the parts summarised here.

## Dependencies

```bash
uv add fastapi pydantic-settings "pydantic[email]" "sqlalchemy[asyncio]" asyncpg pyjwt "pwdlib[argon2]" python-multipart anyio
uv add --dev pytest pytest-asyncio httpx aiosqlite
uv add --dev uvicorn  # or "fastapi[standard]" for the fastapi CLI
```

- **PyJWT and pwdlib**, not `python-jose` and `passlib`: both are unmaintained, and `passlib` breaks with current `bcrypt`. FastAPI's own docs moved to PyJWT and pwdlib with Argon2.
- `python-multipart` is required by `OAuth2PasswordRequestForm`; `anyio` runs password hashing in a worker thread. FastAPI already depends on it, but code that imports a package declares it.
- Leave version bounds to uv and **commit `uv.lock`**: the lock pins what runs, and loose bounds let uv pick per-Python versions (current `pydantic-settings` 2.16 and SQLAlchemy 2.1 need Python 3.11; with `requires-python = ">=3.10"` uv resolves older ones for 3.10). `example/uv.lock` is committed and CI runs with `--locked`.

## Project Structure

```text
src/my_app/
├── main.py                  # create_app() factory and lifespan
├── config.py                # Settings(BaseSettings)
├── database.py              # DeclarativeBase, session factory
├── exceptions.py            # AppError hierarchy (no HTTP here)
├── models/user.py           # SQLAlchemy ORM models
├── schemas/user.py          # Pydantic request/response models
├── api/
│   ├── deps.py              # settings, session, services, current user
│   ├── exceptions.py        # AppError -> HTTP status, in one place
│   └── routes/
│       ├── auth.py
│       └── users.py
├── services/user_service.py         # business rules, no FastAPI imports
└── repositories/user_repository.py  # queries, commits, IntegrityError -> ConflictError
tests/
├── conftest.py              # app + fresh database per test
├── factories.py             # test data through the public API
└── integration/test_users_api.py
```

Dependencies flow inward: routes → services → repositories. Run the app with `uv run uvicorn my_app.main:create_app --factory --reload`.

---

## App Factory

No module-level `app`, no module-level `settings`: the factory takes both, so tests build an app on their own settings and engine without patching anything.

```python
# src/my_app/main.py
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
```

## Configuration

```python
# src/my_app/config.py
"""Application settings loaded from the environment."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration, validated once when the app is created."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "My App"
    database_url: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "my-app"
    access_token_expire_minutes: int = 30
    allowed_origins: list[str] = ["http://localhost:3000"]
```

`SecretStr` keeps the key out of logs and reprs; read it with `.get_secret_value()` where it is used. The settings object travels on `app.state` and reaches handlers through `Depends(get_settings)`, never through `from my_app.config import settings`.

## Database and Models

The model (`example/src/my_app/models/user.py`) declares `unique=True` on `email` and `username`, and `database.py` builds the session factory:

```python
# src/my_app/database.py
"""Declarative base and session factory for async SQLAlchemy."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for every ORM model."""


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Build the session factory; attributes stay loaded after commit for async use."""
    return async_sessionmaker(bind=engine, expire_on_commit=False)
```

`expire_on_commit=False` matters under asyncio: an expired attribute would be reloaded lazily, which an async session cannot do implicitly. Create and change tables with Alembic migrations (see the `database-migrations` skill), not `create_all()` at startup.

## Schemas (Pydantic v2)

```python
# src/my_app/schemas/user.py
"""Request and response models for users and tokens."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    """Registration input."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12)
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserUpdate(BaseModel):
    """Partial update: only the fields sent are changed."""

    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=50)

    @field_validator("email", "username")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str | None:
        # A field may be left out, but an explicit null would reach a NOT NULL
        # column. Defaults are not validated, so an omitted field never gets here.
        if value is None:
            raise ValueError("may be omitted, but not set to null")
        return value


class UserResponse(BaseModel):
    """Public view of a user; never carries the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """One page of users plus the total count."""

    total: int
    items: list[UserResponse]


class TokenResponse(BaseModel):
    """OAuth2 bearer token."""

    access_token: str
    token_type: str = "bearer"
```

Separate input (`Create`/`Update`) from output (`Response`) models, and declare `response_model` on every route, so a field such as `hashed_password` can never leak into a response. In an `Update` model, `X | None = None` lets a field be left out but also accepts an explicit `null`; the validator turns that into a 422 instead of a NOT NULL violation in the database.

## Domain Exceptions, Mapped Once

Services raise domain errors; one handler turns them into HTTP responses with a stable `code`. Routes contain no `try/except` and no status numbers.

```python
# src/my_app/exceptions.py
"""Domain exception hierarchy; HTTP status codes are assigned in api/exceptions.py."""


class AppError(Exception):
    """Base exception for the application."""

    code = "APP_ERROR"


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    code = "NOT_FOUND"


class ConflictError(AppError):
    """Raised when a write would break a uniqueness rule."""

    code = "CONFLICT"


class AuthenticationError(AppError):
    """Raised when credentials or a token are invalid."""

    code = "AUTHENTICATION_FAILED"


class PermissionDeniedError(AppError):
    """Raised when the caller may not perform the action."""

    code = "PERMISSION_DENIED"
```

```python
# src/my_app/api/exceptions.py
"""Map domain exceptions to HTTP responses in one place."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from my_app.exceptions import (
    AppError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)

STATUS_BY_ERROR: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
}


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """Return `{"detail", "code"}` with the status mapped from the exception type."""
    status_code = next(
        (code for error_type, code in STATUS_BY_ERROR.items() if isinstance(exc, error_type)),
        status.HTTP_400_BAD_REQUEST,
    )
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc), "code": exc.code},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install the domain exception handler on `app`."""
    app.add_exception_handler(AppError, handle_app_error)
```

## Dependencies

Annotated aliases keep signatures short. The chain stays three levels deep: current user → service → session and settings.

```python
# src/my_app/api/deps.py
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
```

## Routes

```python
# src/my_app/api/routes/users.py
"""User endpoints: thin handlers that validate, delegate and serialize."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from my_app.api.deps import CurrentUserDep, UserServiceDep
from my_app.models.user import User
from my_app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register_user(payload: UserCreate, service: UserServiceDep) -> User:
    return await service.register(payload=payload)


@router.get("/me", response_model=UserResponse, summary="Current user")
async def read_current_user(current_user: CurrentUserDep) -> User:
    return current_user


@router.get("", response_model=UserListResponse, summary="List users")
async def list_users(
    service: UserServiceDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UserListResponse:
    users, total = await service.list_page(offset=offset, limit=limit)
    return UserListResponse(
        total=total, items=[UserResponse.model_validate(user) for user in users]
    )


@router.patch("/{user_id}", response_model=UserResponse, summary="Update own profile")
async def update_user(
    user_id: int, payload: UserUpdate, service: UserServiceDep, current_user: CurrentUserDep
) -> User:
    return await service.update(user_id=user_id, payload=payload, acting_user=current_user)
```

`example/src/my_app/api/routes/auth.py` adds `POST /auth/token` for the OAuth2 password flow, delegating to `UserService.authenticate()`.

## Service Layer

Business rules live here and raise domain errors. It imports nothing from FastAPI, so it can be unit tested with a fake repository. Two details worth copying: Argon2 is slow on purpose, so hashing and verifying run in a worker thread instead of blocking the event loop; and tokens must carry `exp`, `iss` and `sub`, because PyJWT checks an expiry only when one is present.

```python
# src/my_app/services/user_service.py
"""Business rules for registration, authentication and profile updates."""

from datetime import datetime, timedelta, timezone
from functools import cache

import anyio
import jwt
from pwdlib import PasswordHash

from my_app.config import Settings
from my_app.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from my_app.models.user import User
from my_app.repositories.user_repository import UserRepository
from my_app.schemas.user import UserCreate, UserUpdate

PASSWORD_HASH = PasswordHash.recommended()
REQUIRED_TOKEN_CLAIMS = ["exp", "iss", "sub"]


@cache
def _dummy_password_hash() -> str:
    """A hash to verify when the email is unknown, so a miss takes as long as a hit."""
    return PASSWORD_HASH.hash("dummy-password-for-timing")


async def hash_password(password: str) -> str:
    """Hash off the event loop: Argon2 is deliberately slow, CPU-bound work."""
    return await anyio.to_thread.run_sync(PASSWORD_HASH.hash, password)


async def verify_password(password: str, stored_hash: str) -> bool:
    return await anyio.to_thread.run_sync(PASSWORD_HASH.verify, password, stored_hash)


class UserService:
    """User use cases; framework-agnostic and testable without HTTP."""

    def __init__(self, repository: UserRepository, settings: Settings) -> None:
        self._repository = repository
        self._settings = settings

    async def register(self, payload: UserCreate) -> User:
        user = User(
            email=payload.email,
            username=payload.username,
            hashed_password=await hash_password(payload.password),
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
        stored_hash = user.hashed_password if user else _dummy_password_hash()
        is_valid_password = await verify_password(password, stored_hash)
        if user is None or not is_valid_password:
            raise AuthenticationError("Incorrect email or password")
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self._settings.access_token_expire_minutes
        )
        return jwt.encode(
            {"sub": str(user.id), "iss": self._settings.jwt_issuer, "exp": expires_at},
            self._settings.jwt_secret_key.get_secret_value(),
            algorithm=self._settings.jwt_algorithm,
        )

    async def user_from_token(self, token: str) -> User:
        """Resolve a bearer token to an active user.

        The token must carry an expiry and this app's issuer: PyJWT checks `exp`
        only when present, so without `require` a token minted without one,
        or by another service sharing the secret, would be accepted forever.
        """
        try:
            claims = jwt.decode(
                token,
                self._settings.jwt_secret_key.get_secret_value(),
                algorithms=[self._settings.jwt_algorithm],
                issuer=self._settings.jwt_issuer,
                options={"require": REQUIRED_TOKEN_CLAIMS},
            )
            user_id = int(claims["sub"])
        except (jwt.InvalidTokenError, ValueError) as err:
            raise AuthenticationError("Could not validate credentials") from err
        user = await self._repository.get(user_id)
        if user is None:
            raise AuthenticationError("Could not validate credentials")
        if not user.is_active:
            raise PermissionDeniedError("Inactive user")
        return user
```

## Repository

Owns the queries and the commit, and turns the database's uniqueness violation into a domain `ConflictError`. Rely on the unique constraint rather than a "does it exist?" precheck, which races under concurrent requests.

```python
# src/my_app/repositories/user_repository.py
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
```

---

## Testing with httpx and pytest-asyncio

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = ["integration: marks tests requiring external services"]
addopts = "--strict-markers"
```

```python
# tests/conftest.py
"""Fixtures: an app on a fresh in-memory database for every test."""

from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from my_app.config import Settings
from my_app.database import Base
from my_app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite://"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-only-secret-key-of-at-least-32-bytes",
    )


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    # One engine per test, so each test starts on an empty database.
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def client(settings: Settings, engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app(settings=settings, engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

`example/tests/factories.py` registers users and logs in through the API, and `example/tests/integration/test_users_api.py` covers registration, the 409 conflict, the 422 validation error, the 401 challenge, the 403 on someone else's profile and stable pagination; `example/tests/integration/test_jwt_claims.py` rejects tokens without an expiry or with a foreign issuer, and an explicit `null` in an update. A typical test:

```python
async def test_update_user_other_account_returns_403(client: AsyncClient) -> None:
    await register_user(client=client, email="ada@example.com", username="ada")
    other = await register_user(client=client, email="bob@example.com", username="bob")
    headers = await auth_headers(client=client, email="ada@example.com")

    response = await client.patch(
        f"/users/{other['id']}", json={"username": "taken"}, headers=headers
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"
```

`ASGITransport` does not run the app's lifespan; that is why the engine is injected into `create_app()` rather than created in the lifespan. SQLite in memory keeps these tests fast; run the same suite against PostgreSQL (for example a container in CI) before trusting constraint and type behaviour that SQLite does not share.

---

## Anti-Patterns

```python
# Bad: business logic and HTTP translation inside the handler.
@router.post("/users")
async def create_user(payload: UserCreate, session: SessionDep):
    if await session.scalar(select(User).where(User.email == payload.email)):  # races
        raise HTTPException(status_code=400, detail="Email taken")  # magic number
    ...

# Good: thin handler; the repository turns IntegrityError into ConflictError,
# and api/exceptions.py maps it to 409 for every endpoint at once.
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, service: UserServiceDep) -> User:
    return await service.register(payload=payload)


# Bad: settings imported as a global, so tests must patch the module.
from my_app.config import settings

# Good: injected.
def get_settings(request: Request) -> Settings:
    return request.app.state.settings


# Bad: sync session in an async route blocks the event loop.
@router.get("/items")
async def list_items(db: Session = Depends(get_sync_db)):
    return db.query(Item).all()
```

## Checklist

- [ ] Every route declares `response_model` and uses `status.HTTP_*` constants
- [ ] Routes call one service method; no `try/except`, no queries
- [ ] Domain errors inherit from `AppError` and are mapped in `api/exceptions.py`
- [ ] Settings and sessions arrive through `Depends()`, never module globals
- [ ] Paginated queries have an explicit `order_by`
- [ ] Unknown email and wrong password take the same time and return the same 401
- [ ] Tokens require `exp`, `iss` and `sub`; the issuer is checked on decode
- [ ] CPU-bound work (password hashing) runs off the event loop
- [ ] `uv.lock` is committed
- [ ] Schema changes are Alembic migrations
