# Project Structure

## Cookiecutter Reference

- Follow **cookiecutter-data-science** for data projects
- Follow **cookiecutter-pypackage** for libraries
- Consistency over perfection: pick a structure and stick to it

## Standard Layout

```
project/
├── src/
│   └── <package_name>/   # Use src layout with package directory
│       ├── __init__.py
│       ├── main.py        # Application entry point
│       ├── config.py       # Settings (pydantic-settings)
│       ├── exceptions.py   # Custom exception hierarchy
│       ├── models/         # ORM/domain models
│       ├── schemas/        # Pydantic request/response models
│       ├── api/
│       │   ├── deps.py     # Shared dependencies (auth, db session)
│       │   └── routes/     # Route handlers grouped by domain
│       ├── services/       # Business logic layer
│       └── repositories/   # Data access layer
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── unit/               # Fast, isolated tests
│   └── integration/        # Tests with external dependencies
├── docs/                   # Documentation
├── scripts/                # Utilities, migrations, seeds
├── data/                   # If data project: raw/, processed/, external/
├── .env.example            # Environment variables template
├── pyproject.toml          # Dependencies, ruff, pytest config
├── uv.lock                 # Locked dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Module Conventions

- Use **src layout** (`src/<package_name>/`): prevents accidental imports from project root
- `pyproject.toml` is the single source of truth for project metadata, dependencies, and tool config (ruff, pytest)
- Keep `__init__.py` files minimal: only public API exports
- Group by domain/feature, not by technical layer, when the project grows beyond 10 modules

## Configuration

- Use `pydantic-settings` for application config: type-safe, validates on startup
- One `config.py` at the package root with `Settings(BaseSettings)` class
- Load `.env` in development, environment variables in production
- Never import settings as a global; pass via dependency injection or function parameters
