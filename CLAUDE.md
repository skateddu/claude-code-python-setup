## Project Specifications

- **Operating System**: <YOUR_OPERATIVE_SYSTEM>
- **Programming Language**: Python >= 3.10
- **Package Manager**: uv
- **Linter & Formatter**: ruff

## Golden Rule

**Explicit intent and maintainability over brevity.** All code must be immediately understandable to another developer (or yourself in future).

## Naming Conventions

- **Variables, functions**: `snake_case` — descriptive and explicit about scope and purpose
- **Boolean variables**: Use `is_`, `has_`, `can_` prefixes (`is_authenticated`, `has_permission`)
- **Collections**: Use plural nouns (`users`, `orders`, `transactions`)
- **Temporary variables**: Acceptable in comprehensions/loops (`for item in items`)
- **Classes**: `PascalCase` — single noun or noun phrase
- **Constants**: `UPPER_CASE` — module-level immutable values
- **Private members**: `_leading_underscore` — single underscore for internal use only
- **Dunder names**: `__double_underscore__` — reserved for Python magic; avoid unless implementing protocols
- **Acronyms**: Treat as words (`HttpRequest` not `HTTPRequest`, `api_client` not `API_client`)

## File Organization

- One class per file unless classes are tightly coupled
- Imports grouped: Standard library → Third-party → Local application (alphabetical within groups)
- No circular imports: refactor if detected
- Module docstring: brief one-liner describing purpose
- Constants at module top, below imports

## Python Modern Syntax

Prefer Python 3.10+ features when the project targets >= 3.10:

- **Union types**: `X | None` instead of `Optional[X]`, `int | str` instead of `Union[int, str]`
- **Type hints**: use built-in generics (`list[int]`, `dict[str, Any]`, `tuple[str, ...]`) — no `from typing import List, Dict, Tuple`
- **Pattern matching**: use `match/case` for multi-branch dispatch on type or value (replaces long `if/elif` chains)
- **f-strings**: always prefer over `%` formatting or `.format()`
- **Pathlib**: `Path` over `os.path` for file system operations
- **Dataclasses**: use `@dataclass` for simple data containers without validation; use Pydantic `BaseModel` when validation or serialization is needed
- **Walrus operator**: `:=` in `while` loops and `if` conditions where it reduces repetition — don't overuse for readability
- **Exception groups**: `except*` for handling multiple concurrent exceptions (Python 3.11+, use only if target allows)

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Database | PostgreSQL | Default relational database |
| Cache | Redis | Optional, via `redis-py` |
| ORM | SQLAlchemy 2.0 | Async support via `asyncpg` |
| Data Validation | Pydantic | Also used for settings via `pydantic-settings` |
| Task Queue | Celery / ARQ | Celery (sync) or ARQ (async) |
| API | FastAPI | Async, OpenAPI, Pydantic validation |
| CLI | Typer | Command-line interfaces |
| Terminal/Logging | Rich | Rich output and logging |
| Testing | pytest | See `.claude/rules/testing.md` |
| Containers | Docker + docker-compose | Local dev and deployment |
| CI/CD | GitHub Actions | Default pipeline |

Adapt this stack to your project needs. Remove or replace layers that don't apply.
Use each tool per its design intent. Don't force workarounds.

## Common Commands

```bash
# Dependencies
uv sync                             # Install/sync all dependencies
uv add <package>                    # Add a dependency
uv add --dev <package>              # Add a dev dependency
uv remove <package>                 # Remove a dependency

# Testing
uv run pytest                       # Run all tests
uv run pytest tests/test_mod.py -v  # Run specific file, verbose
uv run pytest -k "test_name" -v     # Run tests matching pattern
uv run pytest --cov=src             # Run with coverage report

# Linting & Formatting
uv run ruff check .                 # Lint
uv run ruff check . --fix           # Lint + auto-fix
uv run ruff format .                # Format
```

## Detailed Rules

Coding standards are organized in `.claude/rules/` by topic:

- @.claude/rules/api-patterns.md
- @.claude/rules/architecture.md
- @.claude/rules/documentation.md
- @.claude/rules/exception-handling.md
- @.claude/rules/git-workflow.md
- @.claude/rules/project-structure.md
- @.claude/rules/security.md
- @.claude/rules/testing.md
