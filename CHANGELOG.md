# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Tests** (`tests/`): 65 tests covering the six hook scripts. Each runs the real script in a subprocess against a crafted payload and asserts on the decision it emits — nothing is mocked, since "the hook silently stopped firing" is the regression worth catching. Both hook bugs this project has shipped were **logic** errors, not shell errors, and neither `shellcheck` nor `validate_config.py` can see that class of fault. Validated by mutation: reintroducing the pre-v1.3.0 `\b` boundary in `protect-main.sh` turns 8 tests red in both directions — `rm -rf /`, `rm -rf .`, `rm -rf ~` slipping through, and `rm -rf .git`, `rm -rf ~/tmp-dir` wrongly blocked. Two paths are deliberately uncovered and documented as such: `verify.sh`'s ruff/pytest body (running it from inside pytest would recurse) and `auto-lint.sh`'s formatting body (its outcome depends on the surrounding project's ruff `include`)
- **CI** (`.github/workflows/ci.yml`): a GitHub Actions workflow on pull requests and pushes to `main`. Until now nothing verified this repository at all — every PR merged without a single automated check. It runs ruff (lint + format), `shellcheck --severity=warning` over the hook scripts, and a new configuration validator
- **Scripts** (`scripts/validate_config.py`): validates that the configuration this template ships is internally coherent — `settings.json` and the MCP configs parse; hook scripts referenced by `settings.json` exist on disk; `CLAUDE.md`'s `@`-imports resolve; every skill's `SKILL.md` still declares `name` and `description`. All but the first fail **silently** at runtime: a hook whose script was renamed just stops firing, a broken `@`-import drops that rule from Claude's context, and a skill missing frontmatter becomes undiscoverable — none of which surfaces an error. Verified by injecting each fault and confirming a non-zero exit

- **README.md**: a "Bash Sandbox" section documenting Claude Code's OS-enforced filesystem and network isolation for Bash commands, with a paste-ready `sandbox` block for a uv-based Python project (allowlists PyPI and GitHub so `uv sync`/`uv add`/`git` don't prompt; denies reads of `~/.aws/credentials` and `~/.ssh`). Deliberately **not** enabled in `.claude/settings.json`: the sandbox doesn't run on native Windows, and enabling it in checked-in project settings would produce a startup warning for every Windows contributor — so the section recommends user-level settings instead. Documents the two footguns worth knowing up front: there's no built-in credential deny list (only what you list is protected), and the `dangerouslyDisableSandbox` retry can put a failed command back outside the boundary unless `allowUnsandboxedCommands` is `false`
- **README.md**: added `bubblewrap` + `socat` to the optional dependencies table — needed for the sandbox on Linux/WSL2, while macOS uses the built-in Seatbelt framework
- **.env.example** / **README.md**: six Claude Code tuning variables. `BASH_DEFAULT_TIMEOUT_MS` (default `120000`) and `BASH_MAX_OUTPUT_LENGTH` (default `30000`, max `150000`) matter for this template specifically — a test suite running over two minutes gets killed mid-run, and verbose `pytest -v` output can be truncated before the failure summary. The other four are listed as explicit defaults: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (`3`), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (`20`, v2.1.217+), `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` (`200`, v2.1.212+ — shared across the main conversation and every subagent, so parallel research fan-outs draw on one budget; raisable but not disableable, and `/clear` resets it), and `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` (`120000`, v2.1.212+ — how long a main-conversation MCP call runs before moving to a background task; `0` disables, and subagent calls are never backgrounded)

### Removed

- **Commands** (`.claude/commands/code-review.md`): deleted. `/code-review` became a built-in Claude Code command (v2.1.218 runs it as a background subagent, v2.1.223 made `/review` its alias and added reusable effort levels such as `/code-review high`), and a project command of the same name shadows it — the built-in was missing from the session's skill list until the file was removed. The built-in supersedes this copy: it does the same multi-agent diff review and adds effort levels, `--fix`, `--comment`, and `/code-review ultra` for a cloud review. The `code-reviewer` agent and `/review-pr` (which drives it for a formal GitHub review decision) are unaffected

### Fixed

- **Hooks** (`session-start.sh`): `input=$(cat)` assigned the hook payload to a variable the script never read (shellcheck `SC2034`), found by the new CI workflow on its first run. Not a bug — the hook inspects the filesystem, not the payload — but the dead assignment made it look like the payload mattered. Replaced with `cat >/dev/null` plus a comment explaining that stdin is drained so Claude Code's write to the pipe always completes

- **Hooks** (`protect-main.sh`): the broad `rm -rf` guard used `\b` (word-boundary) to close each dangerous target (`/`, `.`, `..`, `~`), which doesn't behave as a token boundary — it matches on any adjacent word character and doesn't match at all at end-of-string. Result: the guard silently let through the most common forms of the command (`rm -rf .`, `rm -rf ..`, `rm -rf /`, `rm -rf ~`, with no trailing space), while also incorrectly blocking legitimate specific targets like `rm -rf .git` or `rm -rf ~/tmp-dir`. Replaced the closing boundary with `($|\s)` so it matches the whole token instead. Verified against both dangerous and legitimate cases by invoking the hook directly with crafted input

- **Settings** (`.claude/settings.json`): the `enforce-uv.sh`/`protect-main.sh` `PreToolUse` entries combined multiple patterns in one `if` string (e.g. `Bash(python *)|Bash(pytest *)|...`); the `if` field holds exactly one permission rule with no `||`/list syntax, so the condition never matched and both hooks silently stopped firing — including `protect-main.sh`'s guardrails against force-push, direct push to main, `git reset --hard`, and broad `rm -rf`. Split each pattern into its own hook handler entry (8 for `enforce-uv.sh`, 2 for `protect-main.sh`), per [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)

- **README.md**: the subagents section claimed nesting goes "up to 5 levels deep". The real default is **3 layers** below the main conversation (raised from 1 in Claude Code v2.1.219); at the limit Claude Code withholds the `Agent` tool so the subagent does the work itself. Documented `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` as the way to change it

- **README.md**: the `/orchestrate` row named the pipeline stages `planner → tdd → code-review → security`, which don't match any agent names. Corrected to the actual agents the command drives: `planner → tdd-guide → code-reviewer → security-reviewer`

### Changed

- **Skills** (`.claude/skills/`): re-synced the ten skills vendored from [anthropics/skills](https://github.com/anthropics/skills) — `claude-api`, `doc-coauthoring`, `docx`, `frontend-design`, `mcp-builder`, `pdf`, `pptx`, `skill-creator`, `webapp-testing`, `xlsx` — against upstream `f17010c`. They were copied on 2026-03-20 and never refreshed, so five months of upstream changes had accumulated:
  - **`claude-api`** was the most consequential: it still told Claude to default to `claude-opus-4-6`, and `shared/models.md` knew nothing of Opus 5, Sonnet 5, or Fable 5 — a reference skill actively steering code toward superseded model IDs. Now defaults to `claude-opus-5`. Upstream also split the per-language docs into directories (`python/claude-api/*.md` in place of a single `python/claude-api.md`), replaced the `*/agent-sdk/` pages with `shared/agent-design.md`, and added the Managed Agents doc set, prompt caching, token counting, and model migration pages
  - **`docx`, `pptx`, `xlsx`** picked up upstream's 2026-07-17 consolidation of the shared `scripts/office/` helpers, which carries security fixes, plus template-format support (`.dotx`, `.potx`, `.xltx`) now reflected in their trigger descriptions
  - **`frontend-design`** was rewritten upstream from "production-grade interfaces" into visual-design direction (aesthetics, typography, avoiding templated defaults)
  - The remaining skills changed only in `LICENSE.txt` (upstream filled in the copyright line) or not at all
- **README.md**: flagged which ten skills are vendored copies from upstream, warned that they don't self-update, and recorded the sync point (`f17010c`, 2026-08-13) so the next refresh has a baseline. Updated the `claude-api`, `docx`, `pptx`, `skill-creator`, and `frontend-design` rows to match their new upstream descriptions
- **README.md**: noted that Claude Code v2.1.200 renamed the `default` permission mode's **label** to "Manual" across the CLI, the VS Code and JetBrains extensions, and the desktop app, and accepts `"manual"` as an alias. The `"default"` value in `.claude/settings.json` stays canonical, so nothing needed migrating — but readers looking for "default" in the `Shift+Tab` cycle wouldn't find it
- **README.md**: replaced the short "many more events" aside in the hooks section with the current count (32) and a list of the events most useful for extending this setup — `PostToolBatch`, `PostToolUseFailure`, `SubagentStart`/`SubagentStop`, `InstructionsLoaded`, `PermissionRequest`/`PermissionDenied`, `ConfigChange`, `FileChanged`
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
