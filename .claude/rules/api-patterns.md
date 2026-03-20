---
paths:
  - "src/api/**/*.py"
  - "src/**/routes/**/*.py"
  - "src/**/routers/**/*.py"
  - "src/**/endpoints/**/*.py"
---

# FastAPI and Pydantic Patterns

## Router Organization

- Group endpoints by domain: `src/api/routes/users.py`, `src/api/routes/orders.py`
- Use `APIRouter` with prefix and tags: `router = APIRouter(prefix="/users", tags=["users"])`
- Keep route handlers thin: validate input, call service, return response
- Separate business logic into service layer, not in route handlers

## Pydantic Models

- Naming: `<Entity>Create`, `<Entity>Update`, `<Entity>Response` (e.g., `UserCreate`, `UserResponse`)
- Separate input models (Create/Update) from output models (Response)
- Use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- Define reusable validators with `@field_validator` or `Annotated` types
- Place models in `src/schemas/` or `src/models/` (separate from ORM models)

## Response Patterns

- Use explicit response models: `@router.get("/users/{id}", response_model=UserResponse)`
- Consistent error responses with `HTTPException` and standard status codes
- Use `status.HTTP_201_CREATED` constants, not magic numbers
- For lists: return `list[ItemResponse]`, add pagination for large collections

## Error Handling

- Define custom exception handlers in `src/api/exceptions.py`
- Map domain exceptions to HTTP status codes in a centralized handler
- Return structured error bodies: `{"detail": "message", "code": "ERROR_CODE"}`
- Never leak internal details (stack traces, SQL errors) in API responses

## Dependency Injection

- Use `Depends()` for shared logic: database sessions, auth, pagination
- Define reusable dependencies in `src/api/deps.py`
- Keep dependency chains shallow (max 2-3 levels)

## Configuration

- Use `pydantic-settings` for app configuration: `class Settings(BaseSettings)`
- Load from environment variables with `.env` support
- Access settings via dependency injection, not global imports
