"""Fixtures for running the hook scripts against crafted payloads."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest

from tests.hook_harness import HOOK_TIMEOUT_SECONDS, HOOKS_DIR, REPO_ROOT, HookResult, RunHook


def _require(executable: str) -> str:
    """Return the path to `executable`, skipping the test when it is absent."""
    resolved = shutil.which(executable)
    if resolved is None:
        pytest.skip(f"{executable} is required to run the hook scripts")
    return resolved


@pytest.fixture(scope="session")
def bash_executable() -> str:
    """Path to bash, which interprets every hook script."""
    return _require("bash")


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
