#!/usr/bin/env bash
# Shared helper for the PreToolUse hooks that pattern-match a Bash or PowerShell command.
#
# A hook receives the whole command string, which mixes code with data. A
# heredoc (Bash) or here-string (PowerShell) body carrying prose — a pull
# request description, a commit message, a generated file — can contain text
# like "&& ruff format --check" or "rm -rf / " that a naive pattern reads as an
# invocation, and the hook denies a command that never intended to run either.
# Stripping those bodies leaves roughly what the shell will actually execute.
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

# Echo stdin with every PowerShell here-string body removed, keeping the line
# that opens it and the line that closes it. A here-string opens with `@'` or
# `@"` as the last thing on a line and closes with `'@` or `"@` at the start of
# a line; code can follow the closer (`'@; git push`), so that line is kept.
#
# An ordinary string can also end a line with `@"` (`$to = "dev@"`), and taking
# it for an opener would hide every following line from the hooks. So `@` must
# start a token (line start, whitespace, `=`, `(` or `,` before it) and sit
# outside any string: an even number of that quote character before it.
strip_here_string_bodies() {
    awk -v quote=\' '
    {
        if (in_body) {
            # PowerShell 7 tolerates an indented closer; 5.1 does not.
            probe = $0
            sub(/^[ \t]+/, "", probe)
            if (substr(probe, 1, 2) == closer) {
                in_body = 0
                print
            }
            next
        }
        if (match($0, "(^|[ \t=(,])@[" quote "\"][ \t]*$")) {
            # The match starts on the character before `@`, unless `@` opens the line.
            opener_start = RSTART + (substr($0, RSTART, 1) == "@" ? 0 : 1)
            quote_char = substr($0, opener_start + 1, 1)
            before_opener = substr($0, 1, opener_start - 1)
            if (gsub(quote_char, "", before_opener) % 2 == 0) {
                closer = quote_char "@"
                in_body = 1
            }
        }
        print
    }
    '
}

# Echo the command from stdin reduced to the code the given tool's shell runs:
# here-string bodies are stripped for PowerShell, heredoc bodies for Bash.
strip_prose_bodies() {
    local tool_name=$1
    if [ "$tool_name" = "PowerShell" ]; then
        strip_here_string_bodies
    else
        strip_heredoc_bodies
    fi
}
