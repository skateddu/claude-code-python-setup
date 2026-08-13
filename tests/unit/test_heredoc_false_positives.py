"""Hook decisions on commands that carry prose in a heredoc body.

A `gh pr create --body "$(cat <<'EOF' … EOF)"` ships a description that can
quote shell commands. Read as code, that text made both PreToolUse hooks deny a
command that never intended to run anything of the kind. The hooks now match
against the command with heredoc bodies stripped.
"""

import pytest

from tests.hook_harness import RunHook, bash_payload

# The exact shape that denied the `gh pr create` for the documentation PR.
PR_BODY_QUOTING_TOOLING = """gh pr create --title "docs: coherence pass" --body "$(cat <<'EOF'
Run the checks locally with:

    uv run ruff check . && ruff format --check . && pytest

The guard also blocks rm -rf / and git push --force origin main.
EOF
)"
"""

# grep is line-based, so text at the start of a line sits in command position as
# far as the patterns are concerned. That is the shape that actually misfires.
COMMIT_MESSAGE_QUOTING_TOOLING = """git commit -F - <<'EOF'
fix: stop the guard from missing these

Reproduce with:
pip install requests
rm -rf / --no-preserve-root
EOF
"""

PROSE_COMMANDS = [
    ("pr body", PR_BODY_QUOTING_TOOLING),
    ("commit message", COMMIT_MESSAGE_QUOTING_TOOLING),
]


@pytest.mark.parametrize(
    ("label", "command"), PROSE_COMMANDS, ids=[label for label, _ in PROSE_COMMANDS]
)
def test_enforce_uv_ignores_tooling_named_in_a_heredoc(
    run_hook: RunHook, label: str, command: str
) -> None:
    result = run_hook("enforce-uv", bash_payload(command))

    assert result.is_silent, f"{label} should pass through, hook emitted: {result.stdout!r}"


@pytest.mark.parametrize(
    ("label", "command"), PROSE_COMMANDS, ids=[label for label, _ in PROSE_COMMANDS]
)
def test_protect_main_ignores_commands_named_in_a_heredoc(
    run_hook: RunHook, label: str, command: str
) -> None:
    result = run_hook("protect-main", bash_payload(command))

    assert result.is_silent, f"{label} should pass through, hook emitted: {result.stdout!r}"


def test_enforce_uv_still_denies_a_command_after_a_heredoc(run_hook: RunHook) -> None:
    """Stripping the body must not blind the hook to code around it."""
    command = "cat <<'EOF' > notes.txt\nsome prose\nEOF\npip install requests\n"

    result = run_hook("enforce-uv", bash_payload(command))

    assert result.permission_decision == "deny"


def test_protect_main_still_denies_a_command_after_a_heredoc(run_hook: RunHook) -> None:
    command = "cat <<'EOF' > notes.txt\nsome prose\nEOF\ngit push --force origin main\n"

    result = run_hook("protect-main", bash_payload(command))

    assert result.permission_decision == "deny"


@pytest.mark.parametrize(
    "opener",
    ["<<EOF", "<<'EOF'", '<<"EOF"', "<<-EOF"],
    ids=["bare", "single-quoted", "double-quoted", "dash"],
)
def test_enforce_uv_strips_every_heredoc_spelling(run_hook: RunHook, opener: str) -> None:
    command = f"cat {opener} > notes.txt\npip install requests\nEOF\n"

    result = run_hook("enforce-uv", bash_payload(command))

    assert result.is_silent, f"{opener} body should be ignored, hook emitted: {result.stdout!r}"
