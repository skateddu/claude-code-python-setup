"""Helpers for driving the hook scripts in `.claude/hooks/`.

The hooks are shell scripts that read a JSON payload on stdin and answer on
stdout, so the tests run each real script in a subprocess and assert on the
decision it emits. Nothing is mocked: a hook that silently stops firing is
exactly the regression these tests exist to catch.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
HOOK_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class HookResult:
    """Outcome of running a hook script.

    Attributes
    ----------
    exit_code
        Process exit status. Hooks exit 0 even when they deny an action: the
        decision travels in the JSON payload, not in the status code.
    stdout
        Raw text the hook wrote to stdout.
    """

    exit_code: int
    stdout: str

    @property
    def payload(self) -> dict[str, Any]:
        """Parsed hook output, or an empty dict when the hook stayed silent."""
        if not self.stdout.strip():
            return {}
        return json.loads(self.stdout)

    @property
    def is_silent(self) -> bool:
        """True when the hook emitted nothing, meaning it took no position."""
        return not self.stdout.strip()

    @property
    def permission_decision(self) -> str | None:
        """`permissionDecision` from a `PreToolUse` hook, if it emitted one."""
        return self.payload.get("hookSpecificOutput", {}).get("permissionDecision")

    @property
    def updated_command(self) -> str | None:
        """Command a `PreToolUse` hook rewrote the call to, if it rewrote one."""
        hook_output = self.payload.get("hookSpecificOutput", {})
        return hook_output.get("updatedInput", {}).get("command")

    @property
    def decision(self) -> str | None:
        """Top-level `decision`, used by `UserPromptSubmit` and `Stop` hooks."""
        return self.payload.get("decision")

    @property
    def reason(self) -> str:
        """Explanation the hook gave, from whichever field carries it."""
        hook_output = self.payload.get("hookSpecificOutput", {})
        return hook_output.get("permissionDecisionReason") or self.payload.get("reason", "")

    @property
    def additional_context(self) -> str:
        """Context a `SessionStart` hook injected into the session."""
        return self.payload.get("hookSpecificOutput", {}).get("additionalContext", "")


RunHook = Callable[..., HookResult]


def bash_payload(command: str) -> dict[str, Any]:
    """Build the `PreToolUse` payload Claude Code sends for a Bash call.

    Parameters
    ----------
    command
        The shell command Claude proposed to run.

    Returns
    -------
    dict[str, Any]
        Payload shaped like the real hook input.
    """
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def edit_payload(file_path: str) -> dict[str, Any]:
    """Build the `PostToolUse` payload Claude Code sends after an Edit or Write.

    Parameters
    ----------
    file_path
        Path of the file the tool touched.

    Returns
    -------
    dict[str, Any]
        Payload shaped like the real hook input.
    """
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path}}
