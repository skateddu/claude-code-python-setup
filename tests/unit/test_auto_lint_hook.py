"""Behaviour of the `auto-lint` PostToolUse hook.

The guard clauses cover the conditions under which the hook must do nothing.
The scope tests run real ruff against a deliberately misformatted file: one
outside the project must be left alone, one inside it must be formatted.
"""

from collections.abc import Iterator
from pathlib import Path
import uuid

import pytest

from tests.hook_harness import REPO_ROOT, RunHook, edit_payload

MISFORMATTED_SOURCE = "value=1\n"
FORMATTED_SOURCE = "value = 1\n"


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


def test_auto_lint_leaves_files_outside_the_project_alone(
    run_hook: RunHook, tmp_path: Path
) -> None:
    """An edit to a scratch file was rewritten under this project's ruff rules."""
    outside_file = tmp_path / "scratch.py"
    outside_file.write_text(MISFORMATTED_SOURCE, encoding="utf-8")

    result = run_hook("auto-lint", edit_payload(str(outside_file)), project_dir=REPO_ROOT)

    assert result.is_silent
    assert outside_file.read_text(encoding="utf-8") == MISFORMATTED_SOURCE


@pytest.fixture
def file_inside_project() -> Iterator[Path]:
    """A misformatted file under tests/, removed afterwards whatever happens."""
    path = REPO_ROOT / "tests" / f"_auto_lint_probe_{uuid.uuid4().hex}.py"
    path.write_text(MISFORMATTED_SOURCE, encoding="utf-8")
    yield path
    path.unlink(missing_ok=True)


def test_auto_lint_formats_files_inside_the_project(
    run_hook: RunHook, file_inside_project: Path, tmp_path: Path
) -> None:
    """Forward slashes against the project dir's native spelling: still inside.

    The hook runs from an unrelated directory, as after Claude's `cd`, and must
    still format with the project's ruff from the project root.
    """
    result = run_hook(
        "auto-lint",
        edit_payload(file_inside_project.as_posix()),
        cwd=tmp_path,
        project_dir=REPO_ROOT,
    )

    assert "Auto-formatted" in result.stdout
    assert file_inside_project.read_text(encoding="utf-8") == FORMATTED_SOURCE
