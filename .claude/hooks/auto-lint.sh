#!/usr/bin/env bash
# PostToolUse hook (Edit|Write): auto-formats Python files with ruff after edits.
# Runs ruff check --fix and ruff format silently. Outputs a message only if changes were made.
#
# Requires: jq, uv, ruff (as dev dependency)
set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[ -z "$file_path" ] && exit 0

# Only process Python files
[[ "$file_path" != *.py ]] && exit 0

# Skip if file doesn't exist (e.g., deleted)
[ ! -f "$file_path" ] && exit 0

# Capture file state before linting
before=$(md5sum "$file_path" 2>/dev/null || true)

# Run ruff check with auto-fix (quiet, don't fail the hook)
uv run ruff check --fix --quiet "$file_path" 2>/dev/null || true

# Run ruff format (quiet, don't fail the hook)
uv run ruff format --quiet "$file_path" 2>/dev/null || true

# Check if file changed
after=$(md5sum "$file_path" 2>/dev/null || true)

if [ "$before" != "$after" ]; then
    echo "Auto-formatted $(basename "$file_path") with ruff."
fi
