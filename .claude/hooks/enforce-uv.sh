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
allow_rewrite() {
    jq -nc --arg cmd "$1" --arg reason "$2" \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: $reason, updatedInput: {command: $cmd}}}'
    exit 0
}

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')
tool_name=$(echo "$input" | jq -r '.tool_name // empty')

[ -z "$command" ] && exit 0

# Match against the code the shell will run, not against prose carried in a
# heredoc or here-string body. Rewrites below still emit the original command.
scannable=$(printf '%s\n' "$command" | strip_prose_bodies "$tool_name")

# Skip if already using uv
[[ "$scannable" == *"uv run"* || "$scannable" == *"uv add"* || "$scannable" == *"uv remove"* || "$scannable" == *"uv sync"* || "$scannable" == *"uv pip"* || "$scannable" == *"uvx "* ]] && exit 0

# Windows' `py` launcher picks an interpreter on its own, outside uv's managed
# environment. A version selector (`py -3.12`, `py -V:3.12`) corresponds to uv's
# `--python`, but its suffixes (`-3.12-32`, `-V:Company/Tag`) have no reliable
# translation, so it is denied with the equivalent rather than rewritten.
if echo "$scannable" | grep -qE '^\s*py\s+-(V:|[0-9])'; then
    deny "Use \`uv run --python <version> python ...\` instead of the py launcher's version selector (e.g. \`py -3.12 x.py\` -> \`uv run --python 3.12 python x.py\`)."
fi

# Rewrite a simple `py` invocation to `uv run python`, keeping its arguments.
# `py -m pip` falls through to the pip deny rules below.
if echo "$scannable" | grep -qE '^\s*py(\s|$)' \
    && ! echo "$scannable" | grep -qE '^\s*py\s+-m\s+pip\b'; then
    trimmed=${command#"${command%%[![:space:]]*}"}
    allow_rewrite "uv run python${trimmed#py}" "Rewrote the py launcher to run under uv's managed environment: uv run python${trimmed#py}"
fi

# Auto-rewrite a simple, single bare-tool invocation (command starts with the tool)
# to run under uv. Compound commands and pip are left to the deny rules below, where
# the right transformation is ambiguous (e.g. pip install -e . is not uv add).
if echo "$scannable" | grep -qE '^\s*(python3?|pytest|ruff|mypy|bandit)\b' \
    && ! echo "$scannable" | grep -qE '^\s*python3?\s+-m\s+pip\b'; then
    trimmed=$(echo "$command" | sed -E 's/^[[:space:]]+//')
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
