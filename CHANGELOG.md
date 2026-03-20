# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
