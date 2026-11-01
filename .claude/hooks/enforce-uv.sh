#!/usr/bin/env bash
# PreToolUse hook (Bash, PowerShell): blocks bare Python tool commands and suggests uv equivalents.
# Ensures all Python tooling runs through uv's managed environment.
#
# Requires: jq (https://jqlang.github.io/jq/)
set -euo pipefail

# shellcheck source=lib/command-text.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/command-text.sh"

# Emit a PreToolUse "deny" decision in the current hook output format and exit.
# See https://code.claude.com/docs/en/hooks (PreToolUse uses hookSpecificOutput).
deny() {
    jq -nc --arg reason "$1" \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
}

# Emit a PreToolUse "allow" decision that rewrites the command via updatedInput, then exit.
# Lets a simple bare invocation run under uv instead of being blocked outright.
# updatedInput replaces the whole tool input, so the original fields (timeout,
# run_in_background, description) are carried over and only `command` changes.
allow_rewrite() {
    printf '%s' "$input" | jq -c --arg cmd "$1" --arg reason "$2" \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: $reason, updatedInput: ((.tool_input // {}) + {command: $cmd})}}'
    exit 0
}

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

[ -z "$command" ] && exit 0

# Match against the code the shell will run, not against prose carried in a
# heredoc or here-string body. Rewrites below still emit the original command.
scannable=$(printf '%s\n' "$command" | strip_prose_bodies "$tool_name")

# No early exit for commands that already use uv: one mention of `uv run`
# anywhere used to wave the whole command through, so `uv sync && pip install x`
# skipped every rule. The rules below match a tool only at the start of the
# command or right after a separator, so `uv run pytest`, `uv add --dev pytest`
# and `uv pip list` never match them, while a bare tool chained after uv does.

# A rewrite answers "allow", which also skips the permission prompt for the
# whole command, so it is only offered for a simple command: one line, no
# separators. Anything chained after the tool (`py x.py && pip install y`)
# would otherwise be approved along with it. Other commands fall through to
# the deny rules below. Separators inside quotes count too: denying a quoted
# `|` with guidance is cheaper than approving a real one.
is_simple_command=false
if [[ "$scannable" != *$'\n'* && "$scannable" != *[\;\&\|]* ]]; then
    is_simple_command=true
fi
trimmed=${command#"${command%%[![:space:]]*}"}

# The `py` launcher's own options and the Python install manager's commands
# manage interpreters rather than run one, so there is nothing to route via uv.
if echo "$scannable" | grep -qE '^\s*py\s+(--list|-0|(install|uninstall|list|help)(\s|$))'; then
    exit 0
fi

# Windows' `py` launcher picks an interpreter on its own, outside uv's managed
# environment. A version selector (`py -3.12`, `py -V:3.12`) corresponds to uv's
# `--python`, but its suffixes (`-3.12-32`, `-V:Company/Tag`) have no reliable
# translation, so it is denied with the equivalent rather than rewritten.
if echo "$scannable" | grep -qE '(^|[;&|]\s*)py\s+-(V:|[1-9])'; then
    deny "Use \`uv run --python <version> python ...\` instead of the py launcher's version selector (e.g. \`py -3.12 x.py\` -> \`uv run --python 3.12 python x.py\`)."
fi

# Rewrite a simple `py` invocation to `uv run python`, keeping its arguments.
# `py -m pip` falls through to the pip deny rules below.
if [ "$is_simple_command" = true ] \
    && echo "$scannable" | grep -qE '^\s*py(\s|$)' \
    && ! echo "$scannable" | grep -qE '^\s*py\s+-m\s+pip\b'; then
    allow_rewrite "uv run python${trimmed#py}" "Rewrote the py launcher to run under uv's managed environment: uv run python${trimmed#py}"
fi

# Auto-rewrite a simple bare-tool invocation (command starts with the tool) to
# run under uv. pip is left to the deny rules below, where the right
# transformation is ambiguous (e.g. pip install -e . is not uv add).
if [ "$is_simple_command" = true ] \
    && echo "$scannable" | grep -qE '^\s*(python3?|pytest|ruff|mypy|bandit)\b' \
    && ! echo "$scannable" | grep -qE '^\s*python3?\s+-m\s+pip\b'; then
    allow_rewrite "uv run $trimmed" "Rewrote to run under uv's managed environment: uv run $trimmed"
fi

# pip install → uv add
if echo "$scannable" | grep -qE '(^|[;&|]\s*)pip3?\s+install\b'; then
    deny "Use \`uv add <package>\` instead of pip install. For dev deps: \`uv add --dev <package>\`. To sync: \`uv sync\`."
fi

# Any other pip usage
if echo "$scannable" | grep -qE '(^|[;&|]\s*)pip3?\s'; then
    deny "Use uv instead of pip. Examples: \`uv add <pkg>\`, \`uv remove <pkg>\`, \`uv sync\`, \`uv pip list\`."
fi

# python -m pip, py -m pip
if echo "$scannable" | grep -qE '(^|[;&|]\s*)(python3?|py)\s+-m\s+pip\b'; then
    deny "Use uv instead of python -m pip / py -m pip. Examples: \`uv add <pkg>\`, \`uv sync\`."
fi

# Bare py launcher inside a compound command → uv run python
if echo "$scannable" | grep -qE '(^|[;&|]\s*)py(\s|$)'; then
    deny "Use \`uv run python ...\` instead of the py launcher. This ensures the correct virtual environment."
fi

# Bare python → uv run python
if echo "$scannable" | grep -qE '(^|[;&|]\s*)python3?\s'; then
    deny "Use \`uv run python ...\` instead of bare python. This ensures the correct virtual environment."
fi

# Bare pytest → uv run pytest
if echo "$scannable" | grep -qE '(^|[;&|]\s*)pytest\b'; then
    deny "Use \`uv run pytest ...\` instead of bare pytest."
fi

# Bare ruff → uv run ruff
if echo "$scannable" | grep -qE '(^|[;&|]\s*)ruff\b'; then
    deny "Use \`uv run ruff ...\` instead of bare ruff."
fi

# Bare mypy → uv run mypy
if echo "$scannable" | grep -qE '(^|[;&|]\s*)mypy\b'; then
    deny "Use \`uv run mypy ...\` instead of bare mypy."
fi

# Bare bandit → uv run bandit
if echo "$scannable" | grep -qE '(^|[;&|]\s*)bandit\b'; then
    deny "Use \`uv run bandit ...\` instead of bare bandit."
fi
