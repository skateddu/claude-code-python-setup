"""Guard clauses of the `auto-lint` PostToolUse hook.

The formatting path itself runs `uv run ruff` against the edited file, which
depends on the surrounding project's ruff configuration deciding whether that
path is in scope. That coupling makes it unsuitable for an assertion here, so
these tests cover the conditions under which the hook must do nothing at all —
the cases where running ruff would be wrong or impossible.
"""

from pathlib import Path

from tests.hook_harness import RunHook, edit_payload


def test_auto_lint_ignores_non_python_file(run_hook: RunHook, tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# Title\n", encoding="utf-8")

    result = run_hook("auto-lint", edit_payload(str(readme)))

    assert result.is_silent
    assert result.exit_code == 0


def test_auto_lint_ignores_deleted_file(run_hook: RunHook, tmp_path: Path) -> None:
    """A file edited then removed must not make the hook fail the tool call."""
    result = run_hook("auto-lint", edit_payload(str(tmp_path / "gone.py")))

    assert result.is_silent
    assert result.exit_code == 0


def test_auto_lint_ignores_payload_without_file_path(run_hook: RunHook) -> None:
    result = run_hook("auto-lint", {"tool_name": "Edit", "tool_input": {}})

    assert result.is_silent
    assert result.exit_code == 0
