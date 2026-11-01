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
