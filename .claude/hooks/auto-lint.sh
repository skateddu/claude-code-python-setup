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

# Echo a path with forward slashes, no trailing slash, and Git Bash's `/c/...`
# spelled `c:/...`, so the Windows spellings of one path compare equal.
normalize_path() {
    local path=${1//\\//}
    path=${path%/}
    if [[ "$path" =~ ^/[A-Za-z]/ ]]; then
        path="${path:1:1}:${path:2}"
    fi
    printf '%s' "$path"
}

# Only format files inside the project: an edit elsewhere (a scratch file, a
# sibling repository) would otherwise be rewritten under this project's ruff
# rules. Claude Code always sets CLAUDE_PROJECT_DIR for hooks.
if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    project_dir=$(normalize_path "$CLAUDE_PROJECT_DIR")
    edited_file=$(normalize_path "$file_path")
    shopt -s nocasematch
    [[ "$edited_file" == "$project_dir"/* ]] || exit 0
    shopt -u nocasematch
    # Run ruff from the project root so it picks up the project's configuration.
    cd "$CLAUDE_PROJECT_DIR"
fi

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
