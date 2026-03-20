# Exception Handling

## Core Principles

- Be specific: catch named exceptions, not bare `except:` clauses
- Provide context in error messages: include relevant data and state information
- Don't silence errors: log or re-raise, never pass silently
- Use custom exceptions for application logic (inherit from Exception or specific built-in exceptions)
- Log exception context before re-raising to preserve debugging information

## Custom Exception Hierarchy

Define a base exception for the application, then specialize:

```python
class AppError(Exception):
    """Base exception for the application."""

class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

class ValidationError(AppError):
    """Raised when input data fails validation."""

class AuthenticationError(AppError):
    """Raised when authentication fails."""

class PermissionDeniedError(AppError):
    """Raised when the user lacks permission for an action."""
```

- Place custom exceptions in `src/exceptions.py` or `src/<module>/exceptions.py`
- Always inherit from `AppError` (or a built-in like `ValueError`) for catchability
- Include relevant context as attributes: `self.resource_id`, `self.field_name`, etc.

## Exception Handling Patterns

- Catch at the **boundary** (API handler, CLI command), not deep in business logic
- Let exceptions propagate naturally through the call stack
- Use `raise ... from err` to preserve the exception chain
- Avoid catch-and-reraise without adding information

## FastAPI Integration

Map domain exceptions to HTTP responses with centralized handlers:

```python
@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

- Define handlers in `src/api/exceptions.py`
- One handler per domain exception type
- Never return raw tracebacks to the client
