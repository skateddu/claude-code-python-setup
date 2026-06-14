#!/usr/bin/env bash
# UserPromptSubmit hook: blocks prompts that appear to contain a hardcoded secret
# (API keys, tokens, private keys) so credentials are not pasted into the session.
# Complements the `deny` read rules in settings.json, which only cover secret files.
#
# Requires: jq
set -euo pipefail

input=$(cat)
prompt=$(echo "$input" | jq -r '.prompt // empty')

[ -z "$prompt" ] && exit 0

# Block the prompt and show the reason to the user, then exit.
block() {
    jq -nc --arg reason "$1" '{decision: "block", reason: $reason}'
    exit 0
}

# High-signal secret patterns, kept specific to avoid false positives.
patterns=(
    'AKIA[0-9A-Z]{16}'                    # AWS access key id
    'ghp_[A-Za-z0-9]{36}'                 # GitHub personal access token
    'gh[osur]_[A-Za-z0-9]{36}'            # GitHub OAuth/server/user/refresh token
    'github_pat_[A-Za-z0-9_]{22,}'        # GitHub fine-grained PAT
    'sk-ant-[A-Za-z0-9_-]{20,}'           # Anthropic API key
    'sk-[A-Za-z0-9]{32,}'                 # OpenAI-style secret key
    'AIza[0-9A-Za-z_-]{35}'               # Google API key
    'xox[baprs]-[A-Za-z0-9-]{10,}'        # Slack token
    '-----BEGIN [A-Z ]*PRIVATE KEY-----'  # PEM private key block
)

for pattern in "${patterns[@]}"; do
    if echo "$prompt" | grep -qE -- "$pattern"; then
        block "Your message looks like it contains a hardcoded secret (matched pattern: ${pattern}). Remove the credential and reference it via an environment variable or a secret manager instead. See .claude/rules/security.md."
    fi
done

exit 0
