"""Behaviour of the `enforce-uv` PreToolUse hook."""

import pytest

from tests.hook_harness import RunHook, bash_payload

# A single bare invocation is rewritten to run under uv rather than blocked.
REWRITTEN_COMMANDS = [
    ("python script.py", "uv run python script.py"),
    ("python3 -c 'print(1)'", "uv run python3 -c 'print(1)'"),
    ("pytest -x tests/", "uv run pytest -x tests/"),
    ("ruff check .", "uv run ruff check ."),
    ("mypy src", "uv run mypy src"),
    ("bandit -r src", "uv run bandit -r src"),
    # Leading whitespace is trimmed so the rewrite stays well formed.
    ("   pytest", "uv run pytest"),
]

# pip has no mechanical uv equivalent, and compound commands are ambiguous to
# rewrite, so both are denied with guidance instead.
DENIED_COMMANDS = [
    "pip install requests",
    "pip3 install -e .",
    "pip list",
    "python -m pip install requests",
    "echo building && python setup.py",
    "cat notes.txt | pytest",
]

# Already correct, or nothing to do with the Python toolchain.
IGNORED_COMMANDS = [
    "uv run pytest",
    "uv sync",
    "uv add requests",
    "uvx ruff check .",
    "uv pip list",
    "git status",
    "ls -la",
]


@pytest.mark.parametrize(("command", "expected"), REWRITTEN_COMMANDS)
def test_enforce_uv_rewrites_bare_invocation(
    run_hook: RunHook, command: str, expected: str
) -> None:
    result = run_hook("enforce-uv", bash_payload(command))

    assert result.permission_decision == "allow"
    assert result.updated_command == expected


@pytest.mark.parametrize("command", DENIED_COMMANDS)
def test_enforce_uv_denies_unrewritable_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("enforce-uv", bash_payload(command))

    assert result.permission_decision == "deny", (
        f"{command!r} should be denied, hook emitted: {result.stdout!r}"
    )


@pytest.mark.parametrize("command", IGNORED_COMMANDS)
def test_enforce_uv_ignores_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("enforce-uv", bash_payload(command))

    assert result.is_silent, f"{command!r} should pass through, hook emitted: {result.stdout!r}"
    assert result.exit_code == 0


def test_enforce_uv_pip_reason_points_at_uv_add(run_hook: RunHook) -> None:
    result = run_hook("enforce-uv", bash_payload("pip install requests"))

    assert "uv add" in result.reason
