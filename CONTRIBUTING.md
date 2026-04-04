# Contributing

Thanks for your interest in contributing to **claude-code-python-setup**!

## How to Contribute

### Reporting Bugs

Open an [issue](https://github.com/skateddu/claude-code-python-setup/issues/new?template=bug_report.md) with:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your OS, Python version, and Claude Code version

### Suggesting Features

Open a [feature request](https://github.com/skateddu/claude-code-python-setup/issues/new?template=feature_request.md) describing the use case and expected behavior.

### Submitting Changes

1. Fork the repository
2. Create a branch from `main`: `git checkout -b feature/your-change`
3. Make your changes
4. Run the verification checks:
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run pytest -x
   ```
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/) format:
   ```
   feat(rules): add new testing pattern for async fixtures
   ```
6. Push and open a Pull Request against `main`

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/claude-code-python-setup.git
cd claude-code-python-setup

# Install dependencies
uv sync

# Verify everything works
uv run ruff check . && uv run ruff format --check .
```

## Coding Standards

- Follow the rules defined in `.claude/rules/`
- Python 3.10+ syntax (see `python-idioms.md`)
- Conventional Commits for all commit messages (see `git-workflow.md`)
- One logical change per PR

## Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
