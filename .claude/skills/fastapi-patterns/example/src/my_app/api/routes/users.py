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
