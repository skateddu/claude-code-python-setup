#!/usr/bin/env bash
# SessionStart hook: surfaces project environment state (uv venv, lockfile freshness)
# into the session context so Claude starts with an accurate picture. Stays silent
# when everything is in order.
#
# Requires: jq
set -euo pipefail

# This hook inspects the filesystem rather than the hook payload, but stdin is
# still drained so Claude Code's write to the pipe always completes.
cat >/dev/null

# Only act inside a uv-managed Python project.
[ -f pyproject.toml ] || exit 0

notes=()

if command -v uv >/dev/null 2>&1; then
    if [ ! -d .venv ]; then
        notes+=("No .venv found — run \`uv sync\` to install dependencies.")
    fi
    if [ ! -f uv.lock ]; then
        notes+=("No uv.lock found — run \`uv lock\` (or \`uv sync\`) to create it.")
    elif [ pyproject.toml -nt uv.lock ]; then
        notes+=("pyproject.toml is newer than uv.lock — run \`uv sync\` to refresh the lockfile.")
    fi
else
    notes+=("uv is not installed — see https://docs.astral.sh/uv/ to set up the environment.")
fi

# Everything in order: stay silent.
[ ${#notes[@]} -eq 0 ] && exit 0

context="Project environment check:"
for note in "${notes[@]}"; do
    context+=$'\n'"- $note"
done

jq -nc --arg ctx "$context" \
    '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
