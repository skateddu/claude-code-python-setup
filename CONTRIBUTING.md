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
4. Run the verification checks — the same ones CI runs, so passing here means passing there:
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run pytest
   ```
   CI additionally runs `shellcheck --severity=warning .claude/hooks/*.sh`. Without a system [shellcheck](https://github.com/koalaman/shellcheck#installing), `uvx --from shellcheck-py shellcheck --severity=warning .claude/hooks/*.sh .claude/hooks/lib/*.sh` runs the same check. If you changed the `fastapi-patterns` skill, also run its example, which CI tests too: `cd .claude/skills/fastapi-patterns/example && uv run --python 3.10 python -m pytest -W error`.
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
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

The hook tests shell out to the scripts in `.claude/hooks/`, so they need `bash` and `jq` on your PATH. Without them the suite skips rather than fails. On Windows they use Git for Windows' bash, found through `CLAUDE_CODE_GIT_BASH_PATH` or next to `git`, never the WSL launcher in `System32`.

## Changing the Hooks

- **Keep the guards fail-closed.** `enforce-uv` and `protect-main` set `"onFailure": "block"` in `settings.json`; a new guard should too, and `tests/unit/test_hook_wiring.py` checks it.
- **Name scripts from the project root.** Hook commands run in Claude's current directory, which follows every `cd`, so a command is `bash "$CLAUDE_PROJECT_DIR/.claude/hooks/<script>.sh"`, never a relative path.
- **Wire both shells.** A guarded program needs an `if` condition under the `Bash` matcher and the `PowerShell` one; `tests/unit/test_powershell_hooks.py` checks the pairs.
- **Add a failing test first.** Each hook test runs the real script against a crafted payload. Before fixing a bypass, add the command to the relevant test list and watch it fail against the current script.
- **Write for bash 3.2**, the macOS `/bin/bash`: no `${var,,}`, `mapfile` or associative arrays. The `test-macos` CI job runs the suite under it.

## Vendored Components

Most of `.claude/agents/`, `commands/` and `skills/` is copied from the upstreams listed under [Credits](README.md#credits). To re-sync one:

1. Diff it against upstream with `diff -r --strip-trailing-cr` (`core.autocrlf` turns every line ending into a difference otherwise).
2. Keep local adaptations — those marked "(adapted)" in the README, and local fixes recorded in `CHANGELOG.md`, such as the retired model ids in `mcp-builder`.
3. Update the "Last synced" column of the Credits table with the upstream commit.

## Coding Standards

- Follow the rules defined in `.claude/rules/`
- Python 3.10+ syntax (see `python-idioms.md`)
- Conventional Commits for all commit messages (see `git-workflow.md`)
- One logical change per PR

## Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
