# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **Tests** (`tests/`): 75 tests covering the six hook scripts. Each runs the real script in a subprocess against a crafted payload and asserts on the decision it emits — nothing is mocked, since "the hook silently stopped firing" is the regression worth catching and a mock cannot fail that way. Validated by mutation: reintroducing the pre-v1.3.0 `\b` boundary in `protect-main.sh` turns 8 tests red in both directions. `verify.sh`'s ruff/pytest body and `auto-lint.sh`'s formatting body are left uncovered on purpose
- **CI** (`.github/workflows/ci.yml`): GitHub Actions workflow on pull requests and pushes to `main`, running ruff (lint + format), `shellcheck --severity=warning` over the hook scripts, and `pytest`. Nothing verified this repository before — every earlier pull request merged without a single automated check
- **README.md**: a "Bash Sandbox" section, with a paste-ready `sandbox` block for a uv-based project. Deliberately not enabled in `.claude/settings.json`: the sandbox does not run on native Windows, and enabling it in checked-in project settings would warn at startup for every Windows contributor
- **README.md**: `bubblewrap` and `socat` added to the optional dependencies table, needed by the sandbox on Linux and WSL2
- **.env.example** / **README.md**: six Claude Code tuning variables — `BASH_DEFAULT_TIMEOUT_MS`, `BASH_MAX_OUTPUT_LENGTH`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` and `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS`. The first two are the ones a pytest-based project hits in practice — a suite over two minutes gets killed mid-run, and verbose output truncates before the failure summary; the rest are recorded at their defaults

### Changed

- **Skills** (`.claude/skills/`): re-synced the ten skills vendored from [anthropics/skills](https://github.com/anthropics/skills) — `claude-api`, `doc-coauthoring`, `docx`, `frontend-design`, `mcp-builder`, `pdf`, `pptx`, `skill-creator`, `webapp-testing`, `xlsx` — against upstream `f17010c`. They had been copied on 2026-03-20 and never refreshed, accumulating five months of upstream change:
  - **`claude-api`** was the consequential one: it still told Claude to default to `claude-opus-4-6`, and its `shared/models.md` predated Opus 5, Sonnet 5 and Fable 5 — a reference skill steering code toward superseded model IDs. Upstream also split the per-language docs into directories, replaced the `*/agent-sdk/` pages with `shared/agent-design.md`, and added the Managed Agents doc set
  - **`docx`, `pptx`, `xlsx`** picked up upstream's 2026-07-17 consolidation of the shared `scripts/office/` helpers, which carries security fixes, plus `.dotx`/`.potx`/`.xltx` template support
  - **`frontend-design`** was rewritten upstream from "production-grade interfaces" into visual-design direction
  - The remaining skills changed only in `LICENSE.txt`, or not at all
- **pyproject.toml**: ruff's `include` was `["pyproject.toml", "src/**/*.py"]`, which matched nothing this repository actually ships, since there is no `src/`. Extended to `tests/**/*.py` and `.claude/statusline.py`, with `tests` added to `known-first-party`. Vendored `.claude/skills/` scripts stay out of scope
- **README.md**: recorded which ten skills are vendored copies from upstream, that they do not self-update, and the sync point (`f17010c`, 2026-08-13) so the next refresh has a baseline. Refreshed the `claude-api`, `docx`, `pptx`, `skill-creator` and `frontend-design` rows to match their new upstream descriptions
- **README.md**: rewrote the passages that narrated change instead of describing the current state — the fullscreen-rendering and background-subagent defaults, the permission-mode label, and the rationale for the hook tests. Change history belongs in this file, not in the README
- **CONTRIBUTING.md**: the contributor verification command ran ruff alone while CI also runs the hook tests, so a contributor could be green locally and red in CI. Aligned both commands, noted that `shellcheck` runs in CI, and recorded that the hook tests need `bash` and `jq` on PATH (they skip without them)
- **README.md**: replaced the "many more events" aside in the hooks section with the current count (32) and the events most useful for extending this setup
- **README.md**: documented that `permissions.defaultMode: "default"` is labeled "Manual" in the interface, with `"manual"` accepted as an alias
- **Settings** (`.claude/settings.json`): added `permissions.defaultMode: "default"` explicitly — same behavior as the implicit default, but now visible and easy to customize
- **Settings** (`.claude/settings.json`): `fallbackModel` refreshed from the stale `claude-sonnet-4-6`/`claude-haiku-4-5` IDs to the current `claude-sonnet-5`/`claude-haiku-4-5-20251001`
- **Hooks** (`enforce-uv.sh`, `protect-main.sh`): added `if` conditions to their `PreToolUse` entries so they only spawn on matching Bash commands (Python/pip tooling, git/rm) instead of every Bash call
- **.env.example**: added `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS="0"` (explicit default; set to `1` to hide Claude Code's own bundled skills and workflows, project `.claude/skills/` is unaffected)
- **.env.example**: `CLAUDE_CODE_NO_FLICKER` default flipped to `1` to match the current Claude Code default
- **README.md**: documented `permissions.disableAutoMode` and `language` as available but intentionally unset — neither has a neutral value that preserves default behavior
- **README.md**: synced the `fallbackModel` example, documented the hook `if` conditional field, updated the `CLAUDE_CODE_NO_FLICKER` and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` rows, and bumped the RTK reference to v0.43.0 with `rtk gain`

### Removed

- **Commands** (`.claude/commands/code-review.md`): deleted, because `/code-review` is now a built-in Claude Code command and a project command of the same name shadows it — the built-in was absent from the session's skill list until this file was removed. The built-in supersedes the copy. The `code-reviewer` agent and `/review-pr` are unaffected

### Fixed

- **Hooks** (`enforce-uv.sh`, `protect-main.sh`): both matched their patterns against the raw command string, so text carried in a heredoc body was read as code. A `gh pr create --body "$(cat <<'EOF' … EOF)"` whose description quoted `ruff format` after an `&&`, or `pip install`, or `rm -rf /` at the start of a line, was denied — the hook blocking a command that never intended to run any of it. Found when `enforce-uv` refused the `gh pr create` for the documentation coherence pass. Both now match against the command with heredoc bodies stripped, via a shared `hooks/lib/command-text.sh`; rewrites still emit the original command. Code before or after a heredoc is unaffected. The deliberate trade is that a heredoc fed to an interpreter (`bash <<EOF`) is no longer inspected — these hooks guard against slips, and a false deny costs real work every time it fires. Covered by `tests/unit/test_heredoc_false_positives.py`
- **.gitignore**: the packaging block's `lib/` and `lib64/` rules were unanchored, so they ignored *any* directory named `lib` anywhere in the tree — silently swallowing `.claude/hooks/lib/` here, and a nested `src/<pkg>/lib/` in any project built from this template. Anchored both to the repository root, where distutils actually writes them
- **Hooks** (`session-start.sh`): `input=$(cat)` assigned the payload to a variable the script never read (shellcheck `SC2034`), caught by the new CI on its first run. Not a bug — the hook inspects the filesystem, not the payload — but the dead assignment implied otherwise. Replaced with `cat >/dev/null` and a comment noting stdin is drained so Claude Code's write to the pipe completes
- **Hooks** (`protect-main.sh`): the broad `rm -rf` guard used `\b` to close each dangerous target (`/`, `.`, `..`, `~`), which does not behave as a token boundary — it matches on any adjacent word character and never matches at end-of-string. The guard let through the most common forms (`rm -rf .`, `rm -rf ..`, `rm -rf /`, `rm -rf ~`) while incorrectly blocking legitimate targets like `rm -rf .git` and `rm -rf ~/tmp-dir`. Replaced with `($|\s)` so it matches the whole token
- **Settings** (`.claude/settings.json`): the `enforce-uv.sh`/`protect-main.sh` `PreToolUse` entries combined multiple patterns in one `if` string; the field holds exactly one permission rule with no `||` or list syntax, so the condition never matched and both hooks silently stopped firing — taking `protect-main.sh`'s force-push, push-to-main, `git reset --hard` and `rm -rf` guards with them. Split each pattern into its own handler entry (8 for `enforce-uv.sh`, 2 for `protect-main.sh`)
- **README.md**: the subagents section claimed nesting goes "up to 5 levels deep"; the default is 3 layers below the main conversation. Documented `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` as the way to change it
- **README.md**: the `/orchestrate` row named stages (`planner → tdd → code-review → security`) matching no agent names. Corrected to the agents the command drives: `planner → tdd-guide → code-reviewer → security-reviewer`
- **README.md**: the optional-dependency table credited `jq` to three hooks; all six parse their payload with it, so a partial install would break the other three
- **README.md**: the project tree and the CI section did not list the workflow's shellcheck and pytest steps, and the ruff scope line omitted `tests/`

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
