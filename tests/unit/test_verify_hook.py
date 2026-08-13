"""Guard clauses of the `verify` Stop hook.

Only the early-exit paths are covered. The hook's main body shells out to
`uv run ruff check .` and `uv run pytest`, and exercising that from inside the
test suite would have it invoke pytest recursively. Provisioning a throwaway uv
project to run it in would need a network install on every CI run, so the
execution path is verified by hand rather than here.
"""

from pathlib import Path

from tests.hook_harness import RunHook


def test_verify_respects_the_loop_guard(run_hook: RunHook) -> None:
    """A Stop triggered by this hook's own block must be allowed to end.

    Without this guard the hook would block every stop it caused, leaving the
    session unable to finish a turn.
    """
    result = run_hook("verify", {"stop_hook_active": True})

    assert result.is_silent
    assert result.exit_code == 0


def test_verify_ignores_non_python_project(run_hook: RunHook, tmp_path: Path) -> None:
    result = run_hook("verify", {"stop_hook_active": False}, cwd=tmp_path)

    assert result.is_silent
    assert result.exit_code == 0
