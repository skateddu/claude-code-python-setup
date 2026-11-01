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
    # Windows' py launcher becomes uv's python, arguments untouched.
    ("py script.py", "uv run python script.py"),
    ("py -c 'print(1)'", "uv run python -c 'print(1)'"),
    ("py -m pytest -x", "uv run python -m pytest -x"),
    ("  py", "uv run python"),
    # Separators inside a quoted string or a file-descriptor redirect separate
    # nothing, so these stay simple and are rewritten.
    ("pytest -x 2>&1", "uv run pytest -x 2>&1"),
    ("ruff check . > report.txt 2>&1", "uv run ruff check . > report.txt 2>&1"),
    (
        "python -c 'import sys; print(sys.prefix)'",
        "uv run python -c 'import sys; print(sys.prefix)'",
    ),
    ('python -c "print(1 | 2)"', 'uv run python -c "print(1 | 2)"'),
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
    "py -m pip install requests",
    # A version selector maps onto uv's --python, which the rewrite cannot fill in.
    "py -3.12 script.py",
    "py -V:3.12 script.py",
    "echo building && py script.py",
    # A rewrite answers "allow" for the whole command, so nothing may be chained
    # after the tool: the pip install would be approved along with it.
    "py x.py && pip install requests",
    "python x.py && pip install requests",
    "pytest; pip install requests",
    # Only the first line could be rewritten, mangling the rest.
    "cd sub\npy x.py",
    "cd sub\npython x.py",
    # A mention of uv used to wave the whole command through.
    "uv run pytest && pip install requests",
    "uv sync && pytest",
    "uvx ruff check . ; python setup.py install",
    # The py launcher's own options only pass alone, not with a chain.
    "py --list && pip install requests",
    "pip install requests\npy list",
    # An embedded command would be approved along with the rewrite.
    "python $(pip install requests)",
    "python x.py `pip install requests`",
    "python <(curl -s https://example.com/x.py)",
    'python -c "$(curl -s https://example.com/x.py)"',
]

# Already correct, or nothing to do with the Python toolchain.
IGNORED_COMMANDS = [
    "uv run pytest",
    "uv sync",
    "uv add requests",
    "uvx ruff check .",
    "uv pip list",
    # Tool names as uv's arguments are not bare invocations.
    "uv add --dev pytest",
    "uv run --with ruff ruff check .",
    "uv run python -m pytest -x",
    "uv tool install pyright",
    "uv sync && uv run pytest",
    "git status",
    "ls -la",
    # Tools whose names merely start with "py".
    "pyright src",
    "pyenv versions",
    # The py launcher's own options and the Python install manager's commands
    # manage interpreters; python would reject them.
    "py --list",
    "py --list-paths",
    "py -0",
    "py -0p",
    "py install 3.13",
    "py list",
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


def test_enforce_uv_rewrite_keeps_the_other_tool_input_fields(run_hook: RunHook) -> None:
    """updatedInput replaces the whole tool input, so a rewrite must carry it over.

    Sending only `command` reset a long test run's timeout to the default and
    moved a background command into the foreground.
    """
    payload = bash_payload("pytest -x")
    payload["tool_input"] |= {
        "timeout": 600000,
        "run_in_background": True,
        "description": "Run the test suite",
    }

    result = run_hook("enforce-uv", payload)

    assert result.payload["hookSpecificOutput"]["updatedInput"] == {
        "command": "uv run pytest -x",
        "timeout": 600000,
        "run_in_background": True,
        "description": "Run the test suite",
    }


def test_enforce_uv_py_version_reason_points_at_uv_python_flag(run_hook: RunHook) -> None:
    result = run_hook("enforce-uv", bash_payload("py -3.12 script.py"))

    assert "--python" in result.reason
