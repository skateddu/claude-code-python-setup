#!/usr/bin/env bash
# PreToolUse hook (Bash): blocks bare Python tool commands and suggests uv equivalents.
# Ensures all Python tooling runs through uv's managed environment.
#
# Requires: jq (https://jqlang.github.io/jq/)
set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

[ -z "$command" ] && exit 0

# Skip if already using uv
[[ "$command" == *"uv run"* || "$command" == *"uv add"* || "$command" == *"uv remove"* || "$command" == *"uv sync"* || "$command" == *"uv pip"* || "$command" == *"uvx "* ]] && exit 0

# pip install → uv add
if echo "$command" | grep -qE '(^|[;&|]\s*)pip3?\s+install\b'; then
    echo '{"decision":"block","reason":"Use `uv add <package>` instead of pip install. For dev deps: `uv add --dev <package>`. To sync: `uv sync`."}'
    exit 0
fi

# Any other pip usage
if echo "$command" | grep -qE '(^|[;&|]\s*)pip3?\s'; then
    echo '{"decision":"block","reason":"Use uv instead of pip. Examples: `uv add <pkg>`, `uv remove <pkg>`, `uv sync`, `uv pip list`."}'
    exit 0
fi

# python -m pip
if echo "$command" | grep -qE '(^|[;&|]\s*)python3?\s+-m\s+pip\b'; then
    echo '{"decision":"block","reason":"Use uv instead of python -m pip. Examples: `uv add <pkg>`, `uv sync`."}'
    exit 0
fi

# Bare python → uv run python
if echo "$command" | grep -qE '(^|[;&|]\s*)python3?\s'; then
    echo '{"decision":"block","reason":"Use `uv run python ...` instead of bare python. This ensures the correct virtual environment."}'
    exit 0
fi

# Bare pytest → uv run pytest
if echo "$command" | grep -qE '(^|[;&|]\s*)pytest\b'; then
    echo '{"decision":"block","reason":"Use `uv run pytest ...` instead of bare pytest."}'
    exit 0
fi

# Bare ruff → uv run ruff
if echo "$command" | grep -qE '(^|[;&|]\s*)ruff\b'; then
    echo '{"decision":"block","reason":"Use `uv run ruff ...` instead of bare ruff."}'
    exit 0
fi

# Bare mypy → uv run mypy
if echo "$command" | grep -qE '(^|[;&|]\s*)mypy\b'; then
    echo '{"decision":"block","reason":"Use `uv run mypy ...` instead of bare mypy."}'
    exit 0
fi

# Bare bandit → uv run bandit
if echo "$command" | grep -qE '(^|[;&|]\s*)bandit\b'; then
    echo '{"decision":"block","reason":"Use `uv run bandit ...` instead of bare bandit."}'
    exit 0
fi
