#!/usr/bin/env bash
# PreToolUse hook (Bash): blocks dangerous git operations and destructive commands.
# Prevents accidental force pushes, direct pushes to main/master, and broad rm -rf.
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

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

[ -z "$command" ] && exit 0

# Block git push --force (suggest --force-with-lease)
if echo "$command" | grep -qE 'git\s+push\s.*(-f\b|--force\b)' && ! echo "$command" | grep -qE -- '--force-with-lease'; then
    deny "Force push is blocked. Use \`--force-with-lease\` if you must overwrite remote history."
fi

# Block direct push to main/master
if echo "$command" | grep -qE 'git\s+push\s+(origin|upstream)\s+(main|master)\b'; then
    deny "Direct push to main/master is blocked. Create a feature branch and open a PR instead."
fi

# Block git reset --hard on main/master
if echo "$command" | grep -qE 'git\s+reset\s+--hard'; then
    deny "git reset --hard discards changes permanently. Consider \`git stash\` or \`git reset --soft\` instead."
fi

# Block broad rm -rf (root, home, current dir, parent dir)
if echo "$command" | grep -qE 'rm\s+-r?f?r?\s+(/\s|/\b|\.\s|\.\b|\.\.\s|\.\.\b|~/|~\b)'; then
    deny "Broad rm -rf is blocked. Be specific about what to delete (e.g., rm -rf node_modules/)."
fi
