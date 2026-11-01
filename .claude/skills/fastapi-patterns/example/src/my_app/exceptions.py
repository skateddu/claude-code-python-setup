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
