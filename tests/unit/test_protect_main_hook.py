"""Behaviour of the `protect-main` PreToolUse hook."""

import pytest

from tests.hook_harness import RunHook, bash_payload

DANGEROUS_COMMANDS = [
    "git push --force origin feature",
    "git push -f origin feature",
    "git push origin main",
    "git push upstream master",
    "git reset --hard HEAD~1",
    "rm -rf /",
    "rm -rf ~",
    "rm -rf ~/",
    "rm -rf .",
    "rm -rf ..",
    "rm -fr .",
]

SAFE_COMMANDS = [
    # --force-with-lease is the sanctioned way to overwrite remote history.
    "git push --force-with-lease origin feature",
    "git push origin feature/some-work",
    "git reset --soft HEAD~1",
    # Specific targets that merely start with a guarded token.
    "rm -rf node_modules/",
    "rm -rf .git",
    "rm -rf ~/tmp-build-dir",
    "rm -rf ./build",
    "ls -la",
    "git status",
]


@pytest.mark.parametrize("command", DANGEROUS_COMMANDS)
def test_protect_main_denies_dangerous_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", bash_payload(command))

    assert result.permission_decision == "deny", (
        f"{command!r} should be blocked, hook emitted: {result.stdout!r}"
    )


@pytest.mark.parametrize("command", SAFE_COMMANDS)
def test_protect_main_allows_safe_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", bash_payload(command))

    assert result.is_silent, f"{command!r} should pass through, hook emitted: {result.stdout!r}"
    assert result.exit_code == 0


def test_protect_main_deny_reason_names_the_alternative(run_hook: RunHook) -> None:
    result = run_hook("protect-main", bash_payload("git push --force origin main"))

    assert "--force-with-lease" in result.reason


def test_protect_main_ignores_payload_without_command(run_hook: RunHook) -> None:
    result = run_hook("protect-main", {"tool_name": "Bash", "tool_input": {}})

    assert result.is_silent
    assert result.exit_code == 0
