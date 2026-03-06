# Documentation Standards

## README.md (Mandatory)

- Always create or update with current project specifications
- Minimum content: title, description, project structure, installation, usage, configuration
- Link to detailed documentation in `docs/` folder
- Keep synchronized with implementation

## Specialized Documentation

- Create `docs/` folder for component-specific guides (data pipelines, AI models, testing, API, deployment)
- Name files descriptively: `testing-guide.md`, `api-reference.md`
- Keep structure flat unless complexity requires subdirectories

## Visual Documentation

- Include Mermaid diagrams for architectural overviews and process flows
- Place high-level diagrams in README.md, detailed ones in `docs/`
- Update diagrams when architecture changes
- One concept per diagram for clarity

## API Documentation

- FastAPI generates OpenAPI docs automatically at `/docs` (Swagger) and `/redoc`
- Add docstrings to route handlers: they appear in the auto-generated docs
- Use `summary` and `description` parameters on route decorators for clarity
- Keep auto-generated docs as the primary API reference; avoid maintaining separate API docs

## Changelog

- Maintain a `CHANGELOG.md` in the project root
- Follow Keep a Changelog format: Unreleased, Added, Changed, Deprecated, Removed, Fixed, Security
- Update changelog with each PR, not retroactively

## Type Annotations (Mandatory)

- All function parameters require type hints
- All function return values require type hints
- Prefer modern union syntax: `X | None` over `Optional[X]`, `int | str` over `Union[int, str]`
- Use built-in generics: `list[int]`, `dict[str, Any]`, `tuple[str, ...]` — avoid `from typing import List, Dict, Tuple`
- Use `from typing import ...` only for types without built-in equivalents (`Any`, `TypeVar`, `Protocol`, `TypedDict`)

## Docstrings (NumPy Format)

- **Functions/Methods**: brief one-liner, then Parameters, Returns, Raises sections
- **Classes**: describe purpose, attributes in Attributes section
- **Modules**: one-liner describing module responsibility
- No docstrings for trivial getters/setters

## Comments

- Comment the "why", not the "what"
- Use for complex algorithms, non-obvious business logic, or workarounds
- No comments at file opening
- Keep comments in sync with code

## Logging (Over Print Statements)

- Use `logging` module with consistent structured format
- Include context information as extra parameters
- Log levels: DEBUG (dev diagnostics), INFO (state changes), WARNING (recoverable issues), ERROR (failures), CRITICAL (system down)
