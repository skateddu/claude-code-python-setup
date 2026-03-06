# Architecture and Design

## Modularity

- Follow separation of concerns: one responsibility per function/class
- Favor composition over inheritance
- Keep functions under 30 lines where reasonable
- Extract repeated logic into reusable utilities

## Application Layers

Follow a layered architecture for non-trivial applications:

- **Routes/Handlers** (`api/routes/`): HTTP interface, input validation, response serialization. Thin: call service, return result
- **Services** (`services/`): business logic, orchestration, domain rules. Framework-agnostic, testable without HTTP
- **Repositories** (`repositories/`): data access, database queries, external API calls. Isolate I/O behind interfaces

Dependencies flow inward: routes → services → repositories. Never import routes from services.

## Dependency Injection

- Use FastAPI `Depends()` to inject services, DB sessions, and auth into route handlers
- Define reusable dependencies in `src/api/deps.py`
- Prefer constructor injection for services: pass repositories as init parameters
- Avoid global state; pass configuration explicitly

## Dependencies

- Prefer standard library unless external library significantly improves code clarity or performance
- Justify all external dependencies in comments or PR description
- Always pin versions in requirements/lock files
- Review dependency licenses before adding to commercial projects

## Performance

- Profile before optimizing: use built-in tools (timeit, cProfile) to identify bottlenecks
- Choose data structures intentionally: `set` for membership tests, `dict` for lookups, `list` for order preservation
- Avoid nested loops without justification; consider vectorization or caching
- Lazy-load heavy dependencies only when needed
- Use `async` for I/O-bound operations in FastAPI; keep CPU-bound work synchronous or offload to workers

## Code Review Criteria

- **Readability**: can another developer understand the purpose in few minutes?
- **Testability**: can the code be unit tested without complex setup?
- **Maintainability**: would you be comfortable debugging this in some months?
- **Performance**: are data structures and algorithms appropriate for scale?
