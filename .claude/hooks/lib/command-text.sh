#!/usr/bin/env bash
# Shared helper for the PreToolUse hooks that pattern-match a Bash command.
#
# A hook receives the whole command string, which mixes code with data. A
# heredoc body carrying prose — a pull request description, a commit message,
# a generated file — can contain text like "&& ruff format --check" or
# "rm -rf / " that a naive pattern reads as an invocation, and the hook denies a
# command that never intended to run either. Stripping heredoc bodies leaves
# roughly what the shell will actually execute.
#
# Deliberate limitation: a heredoc fed to an interpreter (`bash <<EOF`) really is
# executable, and its body is no longer inspected. These hooks are heuristics
# guarding against slips, not an adversary, and a false deny costs real work
# every single time it fires while that bypass costs nothing until someone goes
# looking for it.

# Echo stdin with every heredoc body removed, keeping the line that opens it.
# Handles `<<EOF`, `<<'EOF'`, `<<"EOF"` and the tab-stripping `<<-EOF` form.
strip_heredoc_bodies() {
    awk -v quote=\' '
    BEGIN {
        marker_pattern = "<<-?[ \t]*(\"[^\"]+\"|" quote "[^" quote "]+" quote "|[A-Za-z_][A-Za-z0-9_]*)"
    }
    {
        if (in_body) {
            # `<<-` lets the terminator be indented with tabs.
            probe = $0
            sub(/^\t+/, "", probe)
            if (probe == marker) {
                in_body = 0
            }
            next
        }
        if (match($0, marker_pattern)) {
            marker = substr($0, RSTART, RLENGTH)
            sub(/^<<-?[ \t]*/, "", marker)
            gsub(quote, "", marker)
            gsub(/"/, "", marker)
            in_body = 1
        }
        print
    }
    '
}
