# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed

- **Settings** (`.claude/settings.json`): the `enforce-uv.sh`/`protect-main.sh` `PreToolUse` entries combined multiple patterns in one `if` string (e.g. `Bash(python *)|Bash(pytest *)|...`); the `if` field holds exactly one permission rule with no `||`/list syntax, so the condition never matched and both hooks silently stopped firing — including `protect-main.sh`'s guardrails against force-push, direct push to main, `git reset --hard`, and broad `rm -rf`. Split each pattern into its own hook handler entry (8 for `enforce-uv.sh`, 2 for `protect-main.sh`), per [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)

### Changed

- **Settings** (`.claude/settings.json`): added `permissions.defaultMode: "default"` explicitly — same behavior as the implicit default, but now visible and easy to customize
- **.env.example**: added `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS="0"` (explicit default; set to `1` to hide Claude Code's own bundled skills/workflows, project `.claude/skills/` is unaffected)
- **README.md**: documented `permissions.defaultMode`, and noted `permissions.disableAutoMode`/`language` as available but intentionally unset (both lack a neutral value that preserves default behavior)
- **Settings** (`.claude/settings.json`): `fallbackModel` refreshed from the stale `claude-sonnet-4-6`/`claude-haiku-4-5` IDs to the current `claude-sonnet-5`/`claude-haiku-4-5-20251001`
- **Hooks** (`enforce-uv.sh`, `protect-main.sh`): added `if` conditions to their `PreToolUse` entries so they only spawn on matching Bash commands (Python/pip tooling, git/rm) instead of every Bash call
- **README.md**: synced the `fallbackModel` example; documented the hook `if` conditional field; updated `CLAUDE_CODE_NO_FLICKER` (fullscreen rendering is now default-on, no longer a research preview) and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` (implicit team model replaces `TeamCreate`/`TeamDelete`); noted subagents now run in the background by default; bumped the RTK reference to v0.43.0 and mentioned `rtk gain`
- **.env.example**: `CLAUDE_CODE_NO_FLICKER` default flipped to `1` to match the new Claude Code default

## [1.3.0] - 2026-06-14

### Added

- **pyproject.toml**: `[dependency-groups]` (PEP 735) — `dev` group (`ruff`, `pytest`, `pytest-cov`) installed by default with `uv sync`, plus an opt-in `agents` group (`mypy`, `bandit`, `pip-audit`, `safety`, `vulture`, `autoflake`) for tooling invoked only by on-demand agents (`uv sync --group agents`)
- **Settings** (`.claude/settings.json`): `fallbackModel` chain (`claude-sonnet-4-6`, `claude-haiku-4-5`) so sessions continue on a backup model when the primary is overloaded or unavailable
- **Hooks** (`verify.sh`): `Stop` hook that runs `ruff check` + `pytest` when Claude finishes a turn and, on failure, blocks the stop and feeds the errors back so Claude keeps fixing until the project is green (loop-guarded via `stop_hook_active`)
- **Hooks** (`guard-secrets.sh`): `UserPromptSubmit` hook that blocks prompts containing a hardcoded secret (AWS/GitHub/Google/Slack/Anthropic/OpenAI keys, PEM private keys), complementing the file-level `deny` read rules
- **Hooks** (`session-start.sh`): `SessionStart` hook that checks the uv environment (`.venv` presence, `uv.lock` freshness) and injects the status into the session context
- **.gitattributes**: force `*.sh` to LF so the shell hooks stay runnable on Windows checkouts (`core.autocrlf`)

### Changed

- **Hooks** (`enforce-uv.sh`, `protect-main.sh`): migrate `PreToolUse` output from the deprecated top-level `decision`/`reason` fields to the current `hookSpecificOutput.permissionDecision`/`permissionDecisionReason` format
- **Hooks** (`enforce-uv.sh`): auto-rewrite a simple bare `python`/`pytest`/`ruff`/`mypy`/`bandit` invocation to `uv run ...` via `updatedInput` (PreToolUse `allow`) instead of blocking it; `pip` and compound commands still deny with guidance
- **Agents** (`pr-test-analyzer`, `silent-failure-hunter`, `type-design-analyzer`): replace hardcoded "Daisy" persona in `description` examples with a generic user reference
- **README.md**: document the PEP 735 dependency groups as a setup step; sync with recent Claude Code releases (subagent nesting up to 5 levels deep, the full `permissionDecision` set with `updatedInput`, additional hook events, the new `fallbackModel` setting); add `.gitattributes` to the project structure tree
- **CLAUDE.md**: clarify the dependency commands — `uv sync` installs the default `dev` group only; add `uv sync --group agents` for the opt-in agent tooling

### Fixed

- **protect-main.sh**: `git push --force-with-lease` was blocked instead of allowed because `grep` parsed the `--force-with-lease` pattern as an option; pass `--` to end option parsing so the exclusion works as intended

## [1.2.0] - 2026-04-24

### Added

- **Git workflow rules** (`.claude/rules/git-workflow.md`): branching strategy (GitHub Flow) and proactive proposals — agent proposes `git init`, branch creation, commits, push, and PRs instead of acting autonomously; handles existing branch scope detection

### Changed

- **README.md**: simplified RTK install instructions

## [1.1.0] - 2026-04-04

### Added

- **Status line** (`.claude/statusline.py`): Python cross-platform status bar showing model/directory/git info, context usage bar with cost/duration, and rate limit usage bars for 5h/7d windows
- **Permissions** (`.claude/settings.json`): pre-configured `allow` rules for common uv commands and `deny` rules blocking access to sensitive files (.env, secrets, credentials, private keys, SSH keys, certificates, tokens)
- **JSON schema** (`$schema`): added to settings.json for editor autocompletion and validation
- **CONTRIBUTING.md**: guide for contributors — development setup, coding standards, PR workflow
- **CODE_OF_CONDUCT.md**: Contributor Covenant 2.1
- **SECURITY.md**: vulnerability reporting policy

### Changed

- **pyproject.toml**: added `license`, `authors`, `keywords`, `classifiers` (PEP 621 metadata) and `[project.urls]` section (Homepage, Repository, Issues, Changelog)
- **README.md**: status line documented as pre-configured component (was a tip); added Permissions section; added MCP server recommendations with usage guidance; added RTK as recommended optional dependency; added `CLAUDE_CODE_NO_FLICKER` to environment variables table; updated project structure tree with new community files
- **.env.example**: added `CLAUDE_CODE_NO_FLICKER` variable
- **Deny rules**: use explicit environment-specific patterns (`.env.local`, `.env.production`, etc.) instead of broad `.env.*` glob, so `.env.example` remains readable

## [1.0.0] - 2026-03-20

### Added

- **CLAUDE.md**: project instructions file with naming conventions, modern Python syntax, tech stack, common commands, and verification section
- **Rules** (`.claude/rules/`): 10 modular coding standards — api-patterns, architecture, compaction, documentation, exception-handling, git-workflow, project-structure, python-idioms, security, testing
- **Agents** (`.claude/agents/`): 13 specialized subagents — architect, code-architect, code-explorer, code-reviewer, comment-analyzer, database-reviewer, planner, pr-test-analyzer, refactor-cleaner, security-reviewer, silent-failure-hunter, tdd-guide, type-design-analyzer
- **Commands** (`.claude/commands/`): 11 slash commands — build-fix, clean-gone, code-review, commit, commit-push-pr, feature-dev, notebook-review, orchestrate, review-pr, revise-claude-md, test-coverage
- **Skills** (`.claude/skills/`): 22 skills covering API design, Claude API, Claude automation, CLAUDE.md improvement, Django, Docker, databases, document generation, interactive playgrounds, and more
- **Hooks** (`.claude/hooks/`): 3 deterministic guardrails — enforce-uv (blocks bare pip/python/pytest/ruff/mypy/bandit, suggests uv equivalents), auto-lint (runs ruff check + format after Python file edits), protect-main (blocks force push, direct push to main/master, git reset --hard, broad rm -rf)
- **Settings** (`.claude/settings.json`): project-level hook configuration with PreToolUse and PostToolUse event bindings
- **MCP server templates** (`mcp_config/`): pre-configured context7, playwright, postgres, and docker servers for Windows and Linux/Mac
- **Project scaffolding**: pyproject.toml with ruff and pytest config, .python-version, .env.example, .gitignore
