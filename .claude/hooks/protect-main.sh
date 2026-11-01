#!/usr/bin/env bash
# PreToolUse hook (Bash, PowerShell): blocks dangerous git operations and destructive commands.
# Prevents force pushes, pushes to main/master, git reset --hard, and recursive
# deletes of a root, home or working directory (rm -r / Remove-Item -Recurse).
#
# The command is split into subcommands and tokenized rather than matched with
# one regex per rule, because the dangerous forms vary in ways a single
# pattern misses: `git push origin HEAD:main`, `rm -r -f /`, `rm --recursive ~`.
# Quoting is not parsed: quote characters are dropped and every token is
# inspected, so a quoted `git push --force` is still treated as one.
#
# Written for bash 3.2 (macOS's /bin/bash): no ${var,,}, mapfile or assoc arrays.
#
# Requires: jq (https://jqlang.github.io/jq/)
set -euo pipefail

# shellcheck source=lib/command-text.sh
source "$(dirname "${BASH_SOURCE[0]}")/lib/command-text.sh"

PROTECTED_BRANCH_PATTERN='^(refs/heads/)?(main|master)$'

# Emit a PreToolUse "deny" decision in the current hook output format and exit.
# See https://code.claude.com/docs/en/hooks (PreToolUse uses hookSpecificOutput).
deny() {
    jq -nc --arg reason "$1" \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
}

is_protected_branch() {
    [[ "$1" =~ $PROTECTED_BRANCH_PATTERN ]]
}

# Echo the branch checked out in $1, or nothing when HEAD is detached or $1 is
# not a repository.
current_branch() {
    git -C "$1" symbolic-ref --short -q HEAD 2>/dev/null || true
}

# Echo stdin with one subcommand per line: shell separators (&&, ||, ;, |, &)
# and newlines end a subcommand. In Bash, so do parentheses, which open a
# subshell or command substitution. In PowerShell they wrap an argument
# (`Remove-Item -Path (Join-Path $HOME "*")`), so they become spaces and the
# tokens inside stay with the command they feed. awk instead of sed because
# BSD sed has no `\n` in replacements.
split_into_subcommands() {
    local tool_name=$1
    if [ "$tool_name" = "PowerShell" ]; then
        awk '{ gsub(/&&|\|\||[;|&]/, "\n"); gsub(/\$?[()]/, " "); print }'
    else
        awk '{ gsub(/&&|\|\||[;|&()]/, "\n"); print }'
    fi
}

# A recursive delete target is broad when it names a filesystem root, the home
# directory or the working directory, followed by any mix of `/`, `\` and `*`
# (`/`, `~/*`, `/**`, `C:\*`).
is_broad_target() {
    local target=$1
    while [[ -n "$target" && ( "$target" == */ || "$target" == *\\ || "$target" == *\* ) ]]; do
        target=${target%?}
    done

    local is_broad=1
    shopt -s nocasematch
    # Variable names are matched as the literal text Claude wrote, unexpanded.
    # shellcheck disable=SC2016
    case $target in
        "" | "~" | . | .. | [a-z]: | /[a-z]) is_broad=0 ;;
        '$HOME' | '${HOME}' | '$PWD' | '${PWD}') is_broad=0 ;;
        '$env:USERPROFILE' | '$env:HOMEDRIVE' | '$env:SystemDrive') is_broad=0 ;;
    esac
    shopt -u nocasematch
    return "$is_broad"
}

# Deny `git push` that forces, targets main/master, or pushes every branch.
# Without a refspec git pushes the current branch, so that case is resolved
# against the branch checked out in the repository the command runs in.
check_git_push() {
    local repo_dir=$1
    shift
    local is_force=false has_lease=false pushes_every_branch=false
    local positionals=()

    # --force-if-includes only refines a lease and does nothing without one,
    # and --no-force-with-lease cancels any lease given before it.
    while [ $# -gt 0 ]; do
        case $1 in
            --force-with-lease*) has_lease=true ;;
            --no-force-with-lease) has_lease=false ;;
            --force) is_force=true ;;
            --all | --branches | --mirror) pushes_every_branch=true ;;
            -o | --push-option | --repo | --receive-pack | --exec)
                if [ $# -gt 1 ]; then shift; fi
                ;;
            --*) ;;
            -*f*) is_force=true ;;
            -*) ;;
            *) positionals+=("$1") ;;
        esac
        shift
    done

    if [ "$pushes_every_branch" = true ]; then
        deny "Pushing every branch (--all/--mirror) includes main/master. Push the feature branch by name and open a PR instead."
    fi

    local destinations=()
    if [ "${#positionals[@]}" -le 1 ]; then
        destinations+=("HEAD")
    else
        local refspec
        for refspec in "${positionals[@]:1}"; do
            [[ "$refspec" == +* ]] && is_force=true
            refspec=${refspec#+}
            destinations+=("${refspec##*:}")
        done
    fi

    local destination
    for destination in "${destinations[@]}"; do
        if [ "$destination" = "HEAD" ] || [ "$destination" = "@" ]; then
            destination=$(current_branch "$repo_dir")
        fi
        if is_protected_branch "$destination"; then
            deny "Direct push to main/master is blocked. Create a feature branch and open a PR instead."
        fi
    done

    if [ "$is_force" = true ] && [ "$has_lease" = false ]; then
        deny "Force push is blocked. Use \`--force-with-lease\` if you must overwrite remote history."
    fi
}

check_git_reset() {
    local token
    for token in "$@"; do
        if [ "$token" = "--hard" ]; then
            deny "git reset --hard discards changes permanently. Consider \`git stash\` or \`git reset --soft\` instead."
        fi
    done
}

# Echo `path` resolved against `base` unless it is already absolute.
resolve_dir() {
    local base=$1 path=$2
    if [[ "$path" == /* || "$path" =~ ^[A-Za-z]: ]]; then
        echo "$path"
    else
        echo "$base/$path"
    fi
}

# Dispatch the arguments following a `git` token to the subcommand's checks,
# skipping git's global options, including those whose value is a separate
# token (`--git-dir .git`), which would otherwise be read as the subcommand.
# `-C <dir>` and `--git-dir <dir>` move the repository the subcommand acts on,
# which matters for a push that names no branch.
check_git_command() {
    local repo_dir=$1
    shift
    while [ $# -gt 0 ]; do
        case $1 in
            -C | --git-dir)
                [ $# -gt 1 ] || return 0
                repo_dir=$(resolve_dir "$repo_dir" "$2")
                shift 2
                ;;
            --git-dir=*)
                repo_dir=$(resolve_dir "$repo_dir" "${1#--git-dir=}")
                shift
                ;;
            -c | --work-tree | --namespace | --config-env)
                [ $# -gt 1 ] || return 0
                shift 2
                ;;
            -*) shift ;;
            *) break ;;
        esac
    done
    [ $# -gt 0 ] || return 0

    local subcommand=$1
    shift
    case $subcommand in
        push) check_git_push "$repo_dir" "$@" ;;
        reset) check_git_reset "$@" ;;
    esac
}

# Deny a recursive POSIX `rm` of a broad target. Short flags may be clustered
# (-rf, -fR) or separate (-r -f); everything after `--` is a target.
check_rm_command() {
    local is_recursive=false is_end_of_options=false
    local targets=()
    local token
    for token in "$@"; do
        if [ "$is_end_of_options" = false ]; then
            case $token in
                --) is_end_of_options=true; continue ;;
                --recursive) is_recursive=true; continue ;;
                --*) continue ;;
                -*[rR]*) is_recursive=true; continue ;;
                -*) continue ;;
            esac
        fi
        targets+=("$token")
    done

    [ "$is_recursive" = true ] && [ "${#targets[@]}" -gt 0 ] || return 0
    for token in "${targets[@]}"; do
        if is_broad_target "$token"; then
            deny "Broad rm -rf is blocked. Be specific about what to delete (e.g., rm -rf node_modules/)."
        fi
    done
}

# Deny a recursive PowerShell Remove-Item (or one of its aliases) of a broad
# target. Parameter names may be abbreviated to any unique prefix (-r, -rec),
# targets may be comma-separated, and -WhatIf only reports what would go.
check_remove_item_command() {
    local is_recursive=false is_dry_run=false skip_next=false
    local targets=()
    local token parameter
    shopt -s nocasematch
    for token in "$@"; do
        if [ "$skip_next" = true ]; then
            skip_next=false
            continue
        fi
        if [[ "$token" == -* ]]; then
            parameter=${token%%:*}
            # A switch given an explicit `:$false` is off: -WhatIf:$false deletes.
            if [[ "-recurse" == "$parameter"* && "$token" != *:\$false ]]; then
                is_recursive=true
            elif [[ "-whatif" == "$parameter"* && ${#parameter} -ge 2 && "$token" != *:\$false ]]; then
                is_dry_run=true
            elif [[ "$parameter" == -inc* || "$parameter" == -exc* || "$parameter" == -fi* \
                || "$parameter" == -cr* || "$parameter" == -st* ]]; then
                [[ "$token" == *:* ]] || skip_next=true
            elif [[ "$token" == *:* ]]; then
                targets+=("${token#*:}")
            fi
            continue
        fi
        local comma_separated_paths
        IFS=, read -ra comma_separated_paths <<< "$token"
        if [ "${#comma_separated_paths[@]}" -gt 0 ]; then
            targets+=("${comma_separated_paths[@]}")
        fi
    done
    shopt -u nocasematch

    [ "$is_recursive" = true ] && [ "$is_dry_run" = false ] && [ "${#targets[@]}" -gt 0 ] || return 0
    for token in "${targets[@]}"; do
        if is_broad_target "$token"; then
            deny "Broad Remove-Item -Recurse is blocked. Be specific about what to delete (e.g., Remove-Item -Recurse -Force .\\build)."
        fi
    done
}

is_remove_item_name() {
    local name=${1##*\\}
    shopt -s nocasematch
    local is_match=1
    case $name in
        remove-item | rm | ri | del | erase | rd | rmdir) is_match=0 ;;
    esac
    shopt -u nocasematch
    return "$is_match"
}

# `git`, `/usr/bin/git`, `git.exe` or `C:\...\git.exe`.
is_git_name() {
    local name=${1##*[/\\]}
    [ "$name" = "git" ] || [ "$name" = "git.exe" ]
}

# Wrapper options whose value is a user or group name, which may be `git`
# (`sudo -u git rm -rf /`) without being the git program.
is_user_option() {
    case $1 in
        -u | --user | -g | --group | -U | --other-user) return 0 ;;
    esac
    return 1
}

# Run every check that applies to one subcommand's tokens. A guarded program is
# looked for at every position, not only the first, so wrappers (`sudo rm`,
# `bash -c "git push --force"`) are still inspected. After a `git` token, `rm`
# is git's own subcommand (`git rm -r --cached .`) and later words are its
# arguments (`git commit -m "drop rm -rf ."`), not a filesystem delete.
check_subcommand() {
    local tool_name=$1 repo_dir=$2
    shift 2
    local tokens=("$@")
    local index is_after_git=false previous=""
    for ((index = 0; index < ${#tokens[@]}; index++)); do
        local token=${tokens[index]}
        local rest=("${tokens[@]:index+1}")
        local is_value_of_user_option=false
        if is_user_option "$previous"; then
            is_value_of_user_option=true
        fi
        previous=$token
        if is_git_name "$token" && [ "$is_value_of_user_option" = false ]; then
            is_after_git=true
            check_git_command "$repo_dir" ${rest[@]+"${rest[@]}"}
        elif [ "$is_after_git" = true ]; then
            continue
        elif [ "$tool_name" = "PowerShell" ]; then
            if is_remove_item_name "$token"; then
                check_remove_item_command ${rest[@]+"${rest[@]}"}
            fi
        elif [[ "$token" == rm || "$token" == */rm ]]; then
            check_rm_command ${rest[@]+"${rest[@]}"}
        fi
    done
}

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
working_dir=$(echo "$input" | jq -r '.cwd // empty')
[ -n "$working_dir" ] || working_dir=$PWD

[ -z "$command" ] && exit 0

# Match against the code the shell will run, not against prose carried in a
# heredoc or here-string body (a PR description quoting `rm -rf /` is not an
# invocation).
scannable=$(printf '%s\n' "$command" | strip_prose_bodies "$tool_name")

while IFS= read -r subcommand; do
    subcommand=${subcommand//\"/}
    subcommand=${subcommand//\'/}
    read -ra tokens <<< "$subcommand" || true
    [ "${#tokens[@]}" -gt 0 ] || continue
    check_subcommand "$tool_name" "$working_dir" "${tokens[@]}"
done < <(printf '%s\n' "$scannable" | split_into_subcommands "$tool_name")

exit 0
