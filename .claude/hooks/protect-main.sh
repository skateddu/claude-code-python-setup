#!/usr/bin/env bash
# PreToolUse hook (Bash): blocks dangerous git operations and destructive commands.
# Prevents accidental force pushes, direct pushes to main/master, and broad rm -rf.
#
# Requires: jq (https://jqlang.github.io/jq/)
set -euo pipefail

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

[ -z "$command" ] && exit 0

# Block git push --force (suggest --force-with-lease)
if echo "$command" | grep -qE 'git\s+push\s.*(-f\b|--force\b)' && ! echo "$command" | grep -qE '--force-with-lease'; then
    echo '{"decision":"block","reason":"Force push is blocked. Use `--force-with-lease` if you must overwrite remote history."}'
    exit 0
fi

# Block direct push to main/master
if echo "$command" | grep -qE 'git\s+push\s+(origin|upstream)\s+(main|master)\b'; then
    echo '{"decision":"block","reason":"Direct push to main/master is blocked. Create a feature branch and open a PR instead."}'
    exit 0
fi

# Block git reset --hard on main/master
if echo "$command" | grep -qE 'git\s+reset\s+--hard'; then
    echo '{"decision":"block","reason":"git reset --hard discards changes permanently. Consider `git stash` or `git reset --soft` instead."}'
    exit 0
fi

# Block broad rm -rf (root, home, current dir, parent dir)
if echo "$command" | grep -qE 'rm\s+-r?f?r?\s+(/\s|/\b|\.\s|\.\b|\.\.\s|\.\.\b|~/|~\b)'; then
    echo '{"decision":"block","reason":"Broad rm -rf is blocked. Be specific about what to delete (e.g., rm -rf node_modules/)."}'
    exit 0
fi
