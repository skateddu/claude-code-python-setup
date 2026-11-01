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
