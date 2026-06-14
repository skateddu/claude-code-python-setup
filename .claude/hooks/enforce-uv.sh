#!/usr/bin/env bash
# PreToolUse hook (Bash): blocks bare Python tool commands and suggests uv equivalents.
# Ensures all Python tooling runs through uv's managed environment.
#
# Requires: jq (https://jqlang.github.io/jq/)
set -euo pipefail

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

[ -z "$command" ] && exit 0

# Skip if already using uv
[[ "$command" == *"uv run"* || "$command" == *"uv add"* || "$command" == *"uv remove"* || "$command" == *"uv sync"* || "$command" == *"uv pip"* || "$command" == *"uvx "* ]] && exit 0

# Auto-rewrite a simple, single bare-tool invocation (command starts with the tool)
# to run under uv. Compound commands and pip are left to the deny rules below, where
# the right transformation is ambiguous (e.g. pip install -e . is not uv add).
if echo "$command" | grep -qE '^\s*(python3?|pytest|ruff|mypy|bandit)\b' \
    && ! echo "$command" | grep -qE '^\s*python3?\s+-m\s+pip\b'; then
    trimmed=$(echo "$command" | sed -E 's/^[[:space:]]+//')
    allow_rewrite "uv run $trimmed" "Rewrote to run under uv's managed environment: uv run $trimmed"
fi

# pip install → uv add
if echo "$command" | grep -qE '(^|[;&|]\s*)pip3?\s+install\b'; then
    deny "Use \`uv add <package>\` instead of pip install. For dev deps: \`uv add --dev <package>\`. To sync: \`uv sync\`."
fi

# Any other pip usage
if echo "$command" | grep -qE '(^|[;&|]\s*)pip3?\s'; then
    deny "Use uv instead of pip. Examples: \`uv add <pkg>\`, \`uv remove <pkg>\`, \`uv sync\`, \`uv pip list\`."
fi

# python -m pip
if echo "$command" | grep -qE '(^|[;&|]\s*)python3?\s+-m\s+pip\b'; then
    deny "Use uv instead of python -m pip. Examples: \`uv add <pkg>\`, \`uv sync\`."
fi

# Bare python → uv run python
if echo "$command" | grep -qE '(^|[;&|]\s*)python3?\s'; then
    deny "Use \`uv run python ...\` instead of bare python. This ensures the correct virtual environment."
fi

# Bare pytest → uv run pytest
if echo "$command" | grep -qE '(^|[;&|]\s*)pytest\b'; then
    deny "Use \`uv run pytest ...\` instead of bare pytest."
fi

# Bare ruff → uv run ruff
if echo "$command" | grep -qE '(^|[;&|]\s*)ruff\b'; then
    deny "Use \`uv run ruff ...\` instead of bare ruff."
fi

# Bare mypy → uv run mypy
if echo "$command" | grep -qE '(^|[;&|]\s*)mypy\b'; then
    deny "Use \`uv run mypy ...\` instead of bare mypy."
fi

# Bare bandit → uv run bandit
if echo "$command" | grep -qE '(^|[;&|]\s*)bandit\b'; then
    deny "Use \`uv run bandit ...\` instead of bare bandit."
fi
