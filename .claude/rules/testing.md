# Testing Standards

## Test Structure

- Mirror source structure: `src/module.py` → `tests/test_module.py`
- Naming convention: `test_<function>_<scenario>_<expected_result>`
- One logical assertion per test (multiple technical asserts OK if testing same outcome)
- Arrange-Act-Assert pattern: clear separation of setup, execution, verification

## Coverage Requirements

- Minimum 80% line coverage for all modules
- 100% coverage for critical paths: authentication, payments, data integrity, security boundaries
- Focus on behavior, not implementation: test what code does, not how it does it

## Fixtures and Mocking

- Common fixtures: place in `tests/conftest.py`
- Mock external dependencies: APIs, databases, file systems
- Use factories for test data: prefer factory patterns over hardcoded fixtures for complex objects
- Isolate tests: each test must run independently, no shared state

## Test Types and Separation

- **Unit tests**: `tests/unit/` — fast, no I/O, no network, no database
- **Integration tests**: `tests/integration/` — test with real dependencies (DB, APIs)
- Mark slow or integration tests with markers: `@pytest.mark.integration`, `@pytest.mark.slow`
- CI should run unit tests by default, integration tests explicitly

## Pytest Configuration

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests requiring external services",
]
addopts = "-v --strict-markers"
```

## Parametrize Over Duplication

- Use `@pytest.mark.parametrize` for testing multiple inputs against the same logic
- Prefer parametrize over copy-pasting test functions with different values
- Keep parametrize IDs readable: `@pytest.mark.parametrize("input,expected", [...], ids=[...])`
