#!/usr/bin/env bash
# Stop hook: runs ruff and pytest when Claude finishes a turn. On failure, blocks
# the stop and feeds the errors back so Claude keeps fixing until the project is green.
#
# Requires: jq, uv (with the `dev` group: ruff, pytest)
set -euo pipefail

input=$(cat)

# Avoid infinite loops: if this Stop was already triggered by our own block, let it end.
stop_active=$(echo "$input" | jq -r '.stop_hook_active // false')
[ "$stop_active" = "true" ] && exit 0

# Only run inside a uv-managed Python project.
[ -f pyproject.toml ] || exit 0
command -v uv >/dev/null 2>&1 || exit 0

# Emit a Stop "block" decision so Claude continues working, then exit.
block() {
    jq -nc --arg reason "$1" '{decision: "block", reason: $reason}'
    exit 0
}

problems=""

# Lint the whole project.
if ! lint_output=$(uv run ruff check . 2>&1); then
    problems+="ruff check failed:"$'\n'"$lint_output"$'\n\n'
fi

# Run the test suite only when a tests directory exists.
if [ -d tests ]; then
    if ! test_output=$(uv run pytest -x -q 2>&1); then
        problems+="pytest failed:"$'\n'"$test_output"$'\n'
    fi
fi

if [ -n "$problems" ]; then
    # Keep the most relevant (trailing) output so the reason stays readable.
    reason=$(printf '%s' "$problems" | tail -c 3000)
    block "Verification failed before stopping. Fix these issues, then continue:"$'\n\n'"$reason"
fi

exit 0
