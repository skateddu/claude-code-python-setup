# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-03-06

### Added

- **CLAUDE.md**: project instructions file with naming conventions, modern Python syntax, tech stack, and common commands
- **Rules** (`.claude/rules/`): 8 modular coding standards — api-patterns, architecture, documentation, exception-handling, git-workflow, project-structure, security, testing
- **Agents** (`.claude/agents/`): 7 specialized subagents — architect, code-reviewer, database-reviewer, planner, refactor-cleaner, security-reviewer, tdd-guide
- **Commands** (`.claude/commands/`): 6 slash commands — build-fix, notebook-review, orchestrate, review-pr, review-pr-ci, test-coverage
- **Skills** (`.claude/skills/`): 22 skills covering API design, Django, Docker, databases, document generation, and more
- **MCP server templates** (`mcp_config/`): pre-configured context7, playwright, postgres, and docker servers for Windows and Linux/Mac
- **Project scaffolding**: pyproject.toml with ruff and pytest config, .python-version, .env.example, .gitignore
