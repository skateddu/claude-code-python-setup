"""Hook coverage of the PowerShell tool, which Windows sessions use as their shell.

`enforce-uv` and `protect-main` were wired to the Bash tool only, so on Windows
a `pip install` or `git push --force` run through PowerShell skipped both
guards. These tests pin the wiring in `settings.json` and the hooks' decisions
on PowerShell payloads, including here-string bodies, PowerShell's counterpart
to the heredocs that `test_heredoc_false_positives.py` covers.
"""

import json
import re

import pytest

from tests.hook_harness import REPO_ROOT, RunHook, bash_payload, powershell_payload

SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
GUARD_HOOK_COMMANDS = {
    "bash .claude/hooks/enforce-uv.sh",
    "bash .claude/hooks/protect-main.sh",
}
# PowerShell guards deletes as `Remove-Item`, whose rule also matches its `rm`
# alias. `sudo` is wired for both: Windows 11 24H2 and later ship one.
BASH_ONLY_PROGRAMS = {"rm"}
PROTECT_MAIN_COMMAND = "bash .claude/hooks/protect-main.sh"
IF_CONDITION_PATTERN = re.compile(r"^(?P<tool>Bash|PowerShell)\((?P<program>\S+) \*\)$")

DENIED_COMMANDS = [
    ("enforce-uv", "pip install requests"),
    ("enforce-uv", "python -m pip install requests"),
    ("enforce-uv", "Set-Location src; pip install requests"),
    ("enforce-uv", "& python script.py"),
    ("enforce-uv", "py -m pip install requests"),
    ("enforce-uv", "py -3.12 script.py"),
    ("protect-main", "git push --force origin feature"),
    ("protect-main", "git push origin main"),
    ("protect-main", "git reset --hard HEAD~1"),
    ("protect-main", "git fetch; git push -f origin feature"),
]

COMMIT_WITH_SINGLE_QUOTED_HERE_STRING = """git commit -m @'
fix: stop the guard from missing these

Reproduce with:
pip install requests
git push --force origin main
'@
"""

PR_WITH_DOUBLE_QUOTED_HERE_STRING = """gh pr create --title "docs: guards" --body @"
The guard blocks git reset --hard and python -m pip install.
"@
"""

HERE_STRING_COMMANDS = [
    ("single-quoted", COMMIT_WITH_SINGLE_QUOTED_HERE_STRING),
    ("double-quoted", PR_WITH_DOUBLE_QUOTED_HERE_STRING),
]


def _guard_conditions_by_tool() -> dict[str, set[tuple[str, str]]]:
    """Map each tool to the (hook command, guarded program) pairs wired for it."""
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    conditions: dict[str, set[tuple[str, str]]] = {"Bash": set(), "PowerShell": set()}
    for matcher_group in settings["hooks"]["PreToolUse"]:
        for hook in matcher_group["hooks"]:
            if hook["command"] not in GUARD_HOOK_COMMANDS:
                continue
            parsed = IF_CONDITION_PATTERN.match(hook.get("if", ""))
            assert parsed, f"unexpected if condition on {hook['command']}: {hook.get('if')!r}"
            assert parsed["tool"] == matcher_group["matcher"], (
                f"{hook['if']!r} sits under matcher {matcher_group['matcher']!r} and never fires"
            )
            conditions[parsed["tool"]].add((hook["command"], parsed["program"]))
    return conditions


def test_settings_guard_every_bash_program_under_powershell_too() -> None:
    conditions = _guard_conditions_by_tool()
    expected_powershell_conditions = {
        (command, program)
        for command, program in conditions["Bash"]
        if program not in BASH_ONLY_PROGRAMS
    }

    missing = expected_powershell_conditions - conditions["PowerShell"]

    assert not missing, f"guards wired for Bash but not PowerShell: {sorted(missing)}"


def test_settings_guard_remove_item_under_powershell() -> None:
    conditions = _guard_conditions_by_tool()

    assert (PROTECT_MAIN_COMMAND, "Remove-Item") in conditions["PowerShell"]


@pytest.mark.parametrize(("hook_name", "command"), DENIED_COMMANDS)
def test_guard_hooks_deny_powershell_command(
    run_hook: RunHook, hook_name: str, command: str
) -> None:
    result = run_hook(hook_name, powershell_payload(command))

    assert result.permission_decision == "deny", (
        f"{command!r} should be blocked, hook emitted: {result.stdout!r}"
    )


def test_enforce_uv_rewrites_bare_python_in_powershell(run_hook: RunHook) -> None:
    result = run_hook("enforce-uv", powershell_payload("python script.py"))

    assert result.permission_decision == "allow"
    assert result.updated_command == "uv run python script.py"


@pytest.mark.parametrize(
    "hook_name",
    ["enforce-uv", "protect-main"],
)
@pytest.mark.parametrize(
    ("label", "command"),
    HERE_STRING_COMMANDS,
    ids=[label for label, _ in HERE_STRING_COMMANDS],
)
def test_guard_hooks_ignore_tooling_named_in_a_here_string(
    run_hook: RunHook, hook_name: str, label: str, command: str
) -> None:
    result = run_hook(hook_name, powershell_payload(command))

    assert result.is_silent, f"{label} body should be ignored, hook emitted: {result.stdout!r}"


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m @'\nsome prose\n'@; git push --force origin main\n",
        "git commit -m @'\nsome prose\n'@\ngit push --force origin main\n",
    ],
    ids=["same-line-as-closer", "line-after-closer"],
)
def test_protect_main_still_denies_a_command_after_a_here_string(
    run_hook: RunHook, command: str
) -> None:
    """Stripping the body must not blind the hook to code around it."""
    result = run_hook("protect-main", powershell_payload(command))

    assert result.permission_decision == "deny"


@pytest.mark.parametrize(
    "command",
    [
        '$to = "dev@"\ngit push --force origin feature\n',
        "$to = 'dev@'\ngit push --force origin feature\n",
        # `@"` inside a string that is still open is not an opener either.
        '$note = "mail me @"\ngit push --force origin feature\n',
    ],
    ids=["double-quoted-email", "single-quoted-email", "at-inside-open-string"],
)
def test_protect_main_does_not_take_a_string_ending_in_at_for_a_here_string(
    run_hook: RunHook, command: str
) -> None:
    """Mistaking `"dev@"` for an opener would hide every later line."""
    result = run_hook("protect-main", powershell_payload(command))

    assert result.permission_decision == "deny"


def test_guard_hooks_strip_a_here_string_assigned_to_a_variable(run_hook: RunHook) -> None:
    command = '$msg = @"\ngit push --force origin main\n"@\nWrite-Output $msg\n'

    result = run_hook("protect-main", powershell_payload(command))

    assert result.is_silent, f"here-string body should be ignored, hook emitted: {result.stdout!r}"


def test_protect_main_does_not_strip_here_strings_from_bash(run_hook: RunHook) -> None:
    """Here-string stripping is chosen by `tool_name`, so it never runs on Bash.

    Bash payloads keep going through heredoc stripping alone; applying the
    PowerShell rules to them would hide lines no Bash construct hides.
    """
    command = "echo @'\ngit push --force origin main\n'@\n"

    result = run_hook("protect-main", bash_payload(command))

    assert result.permission_decision == "deny"
