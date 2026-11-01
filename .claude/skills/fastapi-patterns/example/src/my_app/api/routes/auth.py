"""Token endpoint for the OAuth2 password flow."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from my_app.api.deps import UserServiceDep
from my_app.schemas.user import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse, summary="Log in")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: UserServiceDep
) -> TokenResponse:
    # OAuth2's form calls the field `username`; this app logs in by email.
    token = await service.authenticate(email=form_data.username, password=form_data.password)
    return TokenResponse(access_token=token)
