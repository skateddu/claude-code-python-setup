"""Hook commands in `settings.json` keep working after Claude changes directory.

Claude Code runs a hook in Claude's current directory, which follows every
`cd`. The commands used to name their script relative to the project root
(`bash .claude/hooks/protect-main.sh`), so after `cd tests` the script was not
found, and a hook that cannot start is a non-blocking error: the force push it
should have denied went ahead. These tests run the configured commands the way
Claude Code does, from a subdirectory, with `CLAUDE_PROJECT_DIR` set.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from tests.hook_harness import (
    HOOK_TIMEOUT_SECONDS,
    REPO_ROOT,
    SETTINGS_PATH,
    HookResult,
    RunHook,
    bash_payload,
    hook_environment,
)

GUARD_SCRIPTS = ("enforce-uv.sh", "protect-main.sh")
SUBDIRECTORY = REPO_ROOT / "tests"


def _hook_handlers() -> list[dict[str, Any]]:
    """Every handler under every event in `settings.json`."""
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return [
        handler
        for matcher_groups in settings["hooks"].values()
        for matcher_group in matcher_groups
        for handler in matcher_group["hooks"]
    ]


def _configured_command(script_name: str) -> str:
    """The first command in `settings.json` that runs `script_name`."""
    return next(
        handler["command"] for handler in _hook_handlers() if script_name in handler["command"]
    )


def _run_configured(
    bash_executable: str, script_name: str, payload: dict[str, Any], cwd: Path
) -> HookResult:
    """Run the configured command for `script_name` as Claude Code would."""
    completed = subprocess.run(
        [bash_executable, "-c", _configured_command(script_name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=hook_environment(project_dir=REPO_ROOT),
        timeout=HOOK_TIMEOUT_SECONDS,
    )
    return HookResult(exit_code=completed.returncode, stdout=completed.stdout)


def _handler_id(handler: dict[str, Any]) -> str:
    """Readable test id: the script name plus the `if` condition, when there is one."""
    script = handler["command"].rsplit("/", 1)[-1].strip('"')
    return f"{script}:{handler['if']}" if "if" in handler else script


@pytest.mark.parametrize("handler", _hook_handlers(), ids=_handler_id)
def test_settings_hook_command_resolves_from_the_project_dir(handler: dict[str, Any]) -> None:
    command = handler["command"]

    assert '"$CLAUDE_PROJECT_DIR/' in command, f"relative hook path breaks after a cd: {command}"


def test_settings_guard_hooks_fail_closed() -> None:
    """A guard that cannot start, times out or crashes must block, not wave through."""
    guards = [
        handler
        for handler in _hook_handlers()
        if any(script in handler["command"] for script in GUARD_SCRIPTS)
    ]

    open_guards = [guard["if"] for guard in guards if guard.get("onFailure") != "block"]

    assert guards
    assert not open_guards, f"guards without onFailure=block: {open_guards}"


def test_configured_protect_main_denies_from_a_subdirectory(bash_executable: str) -> None:
    payload = bash_payload("git push --force origin feature")

    result = _run_configured(bash_executable, "protect-main.sh", payload, cwd=SUBDIRECTORY)

    assert result.exit_code == 0
    assert result.permission_decision == "deny"


def test_configured_enforce_uv_rewrites_from_a_subdirectory(bash_executable: str) -> None:
    result = _run_configured(
        bash_executable, "enforce-uv.sh", bash_payload("pytest -x"), cwd=SUBDIRECTORY
    )

    assert result.updated_command == "uv run pytest -x"


def test_session_start_checks_the_project_root_from_a_subdirectory(
    run_hook: RunHook, tmp_path: Path
) -> None:
    """From a subdirectory there is no pyproject.toml, so the check used to go silent."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    subdirectory = tmp_path / "src"
    subdirectory.mkdir()

    result = run_hook("session-start", {}, cwd=subdirectory, project_dir=tmp_path)

    assert ".venv" in result.additional_context


def test_verify_uses_the_project_root_not_the_current_directory(
    run_hook: RunHook, tmp_path: Path
) -> None:
    """The current directory has a pyproject.toml; the project root does not.

    Verification must follow the project root, so it has nothing to check here.
    Running from the current directory instead would lint and test this
    repository, recursively.
    """
    result = run_hook("verify", {"stop_hook_active": False}, cwd=REPO_ROOT, project_dir=tmp_path)

    assert result.is_silent
    assert result.exit_code == 0
