"""Behaviour of the `session-start` SessionStart hook."""

import os
from pathlib import Path

from tests.hook_harness import RunHook

PAYLOAD = {"session_id": "test-session", "source": "startup"}
PYPROJECT_STUB = '[project]\nname = "demo"\nversion = "0.1.0"\n'


def _make_project(directory: Path) -> Path:
    """Create a minimal uv-style project layout and return its pyproject path."""
    pyproject = directory / "pyproject.toml"
    pyproject.write_text(PYPROJECT_STUB, encoding="utf-8")
    return pyproject


def test_session_start_ignores_non_python_project(run_hook: RunHook, tmp_path: Path) -> None:
    result = run_hook("session-start", PAYLOAD, cwd=tmp_path)

    assert result.is_silent
    assert result.exit_code == 0


def test_session_start_reports_missing_environment(
    run_hook: RunHook, uv_executable: str, tmp_path: Path
) -> None:
    _make_project(tmp_path)

    result = run_hook("session-start", PAYLOAD, cwd=tmp_path)

    assert ".venv" in result.additional_context
    assert "uv.lock" in result.additional_context


def test_session_start_stays_silent_when_environment_is_ready(
    run_hook: RunHook, uv_executable: str, tmp_path: Path
) -> None:
    pyproject = _make_project(tmp_path)
    (tmp_path / ".venv").mkdir()
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text("", encoding="utf-8")
    # The hook compares mtimes, so make the lockfile decisively newer.
    fresh = pyproject.stat().st_mtime + 10
    os.utime(lockfile, (fresh, fresh))

    result = run_hook("session-start", PAYLOAD, cwd=tmp_path)

    assert result.is_silent, f"expected no notes, hook emitted: {result.stdout!r}"


def test_session_start_flags_stale_lockfile(
    run_hook: RunHook, uv_executable: str, tmp_path: Path
) -> None:
    pyproject = _make_project(tmp_path)
    (tmp_path / ".venv").mkdir()
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text("", encoding="utf-8")
    stale = pyproject.stat().st_mtime - 10
    os.utime(lockfile, (stale, stale))

    result = run_hook("session-start", PAYLOAD, cwd=tmp_path)

    assert "uv sync" in result.additional_context
