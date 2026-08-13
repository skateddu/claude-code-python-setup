#!/usr/bin/env bash
# PreToolUse hook (Bash): blocks dangerous git operations and destructive commands.
# Prevents accidental force pushes, direct pushes to main/master, and broad rm -rf.
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

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

[ -z "$command" ] && exit 0

# Match against the code the shell will run, not against prose carried in a
# heredoc body (a PR description quoting `rm -rf /` is not an invocation).
scannable=$(printf '%s
' "$command" | strip_heredoc_bodies)

# Block git push --force (suggest --force-with-lease)
if echo "$scannable" | grep -qE 'git\s+push\s.*(-f\b|--force\b)' && ! echo "$scannable" | grep -qE -- '--force-with-lease'; then
    deny "Force push is blocked. Use \`--force-with-lease\` if you must overwrite remote history."
fi

# Block direct push to main/master
if echo "$scannable" | grep -qE 'git\s+push\s+(origin|upstream)\s+(main|master)\b'; then
    deny "Direct push to main/master is blocked. Create a feature branch and open a PR instead."
fi

# Block git reset --hard on main/master
if echo "$scannable" | grep -qE 'git\s+reset\s+--hard'; then
    deny "git reset --hard discards changes permanently. Consider \`git stash\` or \`git reset --soft\` instead."
fi

# Block broad rm -rf (root, home, current dir, parent dir). The target must be
# followed by whitespace or end-of-string so it matches the whole token, not a
# prefix (e.g. this must not match `rm -rf .git` or `rm -rf ~/tmp-dir`).
if echo "$scannable" | grep -qE 'rm\s+-r?f?r?\s+(\.\.|\.|~/|~|/)($|\s)'; then
    deny "Broad rm -rf is blocked. Be specific about what to delete (e.g., rm -rf node_modules/)."
fi
