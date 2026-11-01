"""Fixtures for running the hook scripts against crafted payloads."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest

from tests.hook_harness import HOOK_TIMEOUT_SECONDS, HOOKS_DIR, REPO_ROOT, HookResult, RunHook

GIT_BASH_PATH_ENV_VAR = "CLAUDE_CODE_GIT_BASH_PATH"


def _require(executable: str) -> str:
    """Return the path to `executable`, skipping the test when it is absent."""
    resolved = shutil.which(executable)
    if resolved is None:
        pytest.skip(f"{executable} is required to run the hook scripts")
    return resolved


def _is_wsl_launcher(bash_path: Path) -> bool:
    """Tell whether `bash_path` is Windows' WSL launcher rather than a real bash.

    `C:\\Windows\\System32\\bash.exe` forwards to a WSL distro, which cannot see
    Windows-side tools such as jq and fails outright when no distro is installed.

    Parameters
    ----------
    bash_path
        Path of a `bash.exe` candidate.

    Returns
    -------
    bool
        True when `bash_path` lives in the Windows `System32` directory.
    """
    system_root = Path(os.environ.get("SYSTEMROOT", r"C:\Windows"))
    return bash_path.resolve().parent == (system_root / "System32").resolve()


def _find_windows_git_bash() -> str | None:
    """Locate Git for Windows' bash, the interpreter Claude Code runs hooks with.

    Checked in order: the `CLAUDE_CODE_GIT_BASH_PATH` override Claude Code also
    honours, the `bin/bash.exe` next to the `git` on PATH, then any bash on PATH
    that is not the WSL launcher.

    Returns
    -------
    str | None
        Path to Git Bash, or None when no usable bash is found.
    """
    override = os.environ.get(GIT_BASH_PATH_ENV_VAR)
    if override and Path(override).is_file():
        return override

    git_path = shutil.which("git")
    if git_path is not None:
        for git_install_dir in Path(git_path).resolve().parents[:3]:
            candidate = git_install_dir / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)

    bash_on_path = shutil.which("bash")
    if bash_on_path is not None and not _is_wsl_launcher(Path(bash_on_path)):
        return bash_on_path
    return None


@pytest.fixture(scope="session")
def bash_executable() -> str:
    """Path to bash, which interprets every hook script.

    On Windows a bare `bash` lookup can resolve to the WSL launcher, so Git
    Bash is located explicitly to match the shell Claude Code uses for hooks.
    """
    if sys.platform != "win32":
        return _require("bash")

    git_bash = _find_windows_git_bash()
    if git_bash is None:
        pytest.skip("Git for Windows' bash is required to run the hook scripts")
    return git_bash


@pytest.fixture(scope="session")
def jq_executable() -> str:
    """Path to jq, which every hook uses to read its payload and build output."""
    return _require("jq")


@pytest.fixture(scope="session")
def uv_executable() -> str:
    """Path to uv, needed by the hooks that inspect or drive the toolchain."""
    return _require("uv")


@pytest.fixture
def run_hook(bash_executable: str, jq_executable: str) -> RunHook:
    """Return a callable that runs a hook script against a payload.

    Returns
    -------
    RunHook
        `run_hook(hook_name, payload, cwd=None)` -> `HookResult`. `hook_name` is
        the script's stem, for example `"protect-main"`. `cwd` defaults to the
        repository root; pass a temp directory for hooks that inspect the
        working directory.
    """

    def _run(
        hook_name: str,
        payload: dict[str, Any],
        cwd: Path | None = None,
    ) -> HookResult:
        script_path = HOOKS_DIR / f"{hook_name}.sh"
        assert script_path.is_file(), f"hook script not found: {script_path}"

        completed = subprocess.run(
            [bash_executable, str(script_path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(cwd or REPO_ROOT),
            timeout=HOOK_TIMEOUT_SECONDS,
        )
        return HookResult(exit_code=completed.returncode, stdout=completed.stdout)

    return _run
