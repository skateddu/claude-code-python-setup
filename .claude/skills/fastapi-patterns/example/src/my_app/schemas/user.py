"""Request and response models for users and tokens."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
