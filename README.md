# Claude Code Python Setup

[![License: MIT](https://img.shields.io/github/license/skateddu/claude-code-python-setup)](LICENSE)
[![Python >= 3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/skateddu/claude-code-python-setup)](https://github.com/skateddu/claude-code-python-setup/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/skateddu/claude-code-python-setup)](https://github.com/skateddu/claude-code-python-setup/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/skateddu/claude-code-python-setup)](https://github.com/skateddu/claude-code-python-setup/commits/main)

A ready-to-use `.claude` configuration for Python development projects with Claude Code. Includes curated agents, commands, skills, and MCP server templates.

## Prerequisites

### Claude Code

Claude Code requires a **Pro, Max, Teams, Enterprise, or Console** account (the free Claude.ai plan does not include Claude Code access).

**System requirements:**

- macOS 13.0+ / Windows 10 1809+ / Ubuntu 20.04+ / Debian 10+
- 4 GB+ RAM
- Internet connection
- On Windows: [Git for Windows](https://git-scm.com/downloads/win) is required

**Installation:**

```bash
# macOS / Linux / WSL
curl -fsSL https://claude.ai/install.sh | bash
```

```powershell
# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

```powershell
# Windows (alternative: WinGet)
winget install Anthropic.ClaudeCode
```

After installation, navigate to your project directory and run `claude` to start. On first run, follow the browser prompts to authenticate.

Verify with:

```bash
claude --version
claude doctor     # detailed check
```

> Full documentation: [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup)

### Optional Dependencies

Some components require additional tools. Install only what you need:

| Dependency | Required by | Install |
|-----------|-------------|---------|
| **Node.js 18+** | context7, playwright MCP servers | [nodejs.org](https://nodejs.org/) |
| **Python >= 3.10 + uv** | postgres, docker MCP servers | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | docker MCP server | [docker.com](https://www.docker.com/get-started/) |
| **PostgreSQL** | postgres MCP server | Running instance (local or remote) |
| **jq** | hooks (enforce-uv, protect-main, auto-lint) | [jqlang.github.io/jq](https://jqlang.github.io/jq/download/) |
| **bubblewrap + socat** | [Bash sandbox](#bash-sandbox-opt-in-not-enabled-here) on Linux/WSL2 only (macOS needs nothing; native Windows unsupported) | your package manager |
| **[RTK](https://github.com/rtk-ai/rtk)** | token optimization (recommended) | [install guide](https://github.com/rtk-ai/rtk#installation) |

> `npx` comes with Node.js. `uvx` comes with uv. No additional installs needed beyond the base tools.

> **Token savings tip**: [RTK (Rust Token Killer)](https://github.com/rtk-ai/rtk) (v0.43.0+) is a CLI proxy that reduces token consumption by 60-90% on common dev commands (git, tests, build, lint). Run `rtk init -g` to install a hook that automatically optimizes all shell commands in Claude Code sessions, then `rtk gain` to see per-command and session token savings.

## Project Structure

```
claude-code-python-setup/
├── .claude/
│   ├── agents/              # Specialized subagents
│   │   ├── architect.md
│   │   ├── code-architect.md
│   │   ├── code-explorer.md
│   │   ├── code-reviewer.md
│   │   ├── comment-analyzer.md
│   │   ├── database-reviewer.md
│   │   ├── planner.md
│   │   ├── pr-test-analyzer.md
│   │   ├── refactor-cleaner.md
│   │   ├── security-reviewer.md
│   │   ├── silent-failure-hunter.md
│   │   ├── tdd-guide.md
│   │   └── type-design-analyzer.md
│   ├── commands/            # Slash commands (/command-name)
│   │   ├── build-fix.md
│   │   ├── clean-gone.md
│   │   ├── commit.md
│   │   ├── commit-push-pr.md
│   │   ├── feature-dev.md
│   │   ├── notebook-review.md
│   │   ├── orchestrate.md
│   │   ├── review-pr.md
│   │   ├── revise-claude-md.md
│   │   └── test-coverage.md
│   ├── hooks/                # Deterministic guardrails
│   │   ├── session-start.sh  # Check uv env (.venv, lockfile) at session start
│   │   ├── guard-secrets.sh  # Block prompts containing hardcoded secrets
│   │   ├── enforce-uv.sh     # Rewrite bare python/pytest to uv run, block pip
│   │   ├── protect-main.sh   # Block force push, direct push to main, broad rm -rf
│   │   ├── auto-lint.sh      # Auto-format Python files with ruff after edits
│   │   └── verify.sh         # Run ruff + pytest on Stop; block until green
│   ├── rules/               # Modular coding standards
│   │   ├── api-patterns.md  # FastAPI/Pydantic (path-scoped)
│   │   ├── architecture.md
│   │   ├── compaction.md
│   │   ├── documentation.md
│   │   ├── exception-handling.md
│   │   ├── git-workflow.md
│   │   ├── project-structure.md
│   │   ├── python-idioms.md
│   │   ├── security.md
│   │   └── testing.md
│   ├── settings.json          # Project-level hooks, permissions, status line
│   ├── statusline.py          # Status line script (Python, cross-platform)
│   └── skills/              # Reference docs and scripts
│       ├── api-design/
│       ├── claude-api/
│       ├── claude-automation-recommender/
│       ├── claude-md-improver/
│       ├── database-migrations/
│       ├── deployment-patterns/
│       ├── django-patterns/
│       ├── django-security/
│       ├── django-tdd/
│       ├── django-verification/
│       ├── doc-coauthoring/
│       ├── docker-patterns/
│       ├── docx/
│       ├── frontend-design/
│       ├── mcp-builder/
│       ├── pdf/
│       ├── playground/
│       ├── postgres-patterns/
│       ├── pptx/
│       ├── skill-creator/
│       ├── webapp-testing/
│       └── xlsx/
├── mcp_config/
│   ├── linux_mac.mcp.json   # MCP server config (Linux/Mac)
│   └── windows.mcp.json     # MCP server config (Windows)
├── .env.example             # Environment variables template
├── .gitattributes           # Force *.sh to LF so hooks run on Windows
├── .gitignore
├── .python-version          # Python version pin for uv
├── CHANGELOG.md             # Version history (Keep a Changelog format)
├── CLAUDE.md                # Project instructions (< 200 lines, imports rules)
├── CODE_OF_CONDUCT.md       # Contributor Covenant 2.1
├── CONTRIBUTING.md          # How to contribute, setup, PR workflow
├── LICENSE                  # MIT License
├── pyproject.toml           # Project metadata, ruff and pytest config
├── README.md
└── SECURITY.md              # Vulnerability reporting policy
```

## Setup

### 1. Copy the `.claude` folder

Copy the `.claude/` directory and `CLAUDE.md` into the root of your project.

Then open `CLAUDE.md` and replace the `<YOUR_OPERATIVE_SYSTEM>` placeholder with your actual OS (e.g., `Windows 11`, `macOS 15`, `Ubuntu 24.04`).

### 2. Configure MCP servers

Copy the appropriate MCP template to `.mcp.json` in your project root:

```bash
# Windows
cp mcp_config/windows.mcp.json .mcp.json

# Linux / Mac
cp mcp_config/linux_mac.mcp.json .mcp.json
```

> `.mcp.json` is gitignored so each developer can use the template matching their OS.

### 3. Set environment variables (optional)

Some components use environment variables for configuration. These must be **system environment variables** (Claude Code does not read `.env` files). See `.env.example` for all available variables and defaults.

```bash
# Linux / Mac — add to ~/.bashrc or ~/.zshrc
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=mydb
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=85
```

```powershell
# Windows — via setx or System Properties > Environment Variables
setx POSTGRES_USER myuser
setx POSTGRES_PASSWORD mypassword
setx POSTGRES_HOST localhost
setx POSTGRES_PORT 5432
setx POSTGRES_DB mydb
setx CLAUDE_AUTOCOMPACT_PCT_OVERRIDE 85
```

| Variable | Used by | Default | Description |
|----------|---------|---------|-------------|
| `POSTGRES_*` | postgres MCP server | see `.env.example` | Database connection parameters |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Claude Code | `95` | Context % threshold that triggers auto-compaction (lower = compacts earlier, reduces response time) |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Claude Code | `0` (disabled) | Set to `1` to enable Agent Teams: spawning a teammate via the Agent tool's `name` parameter implicitly forms a team for the session (no `TeamCreate`/`TeamDelete` setup needed) ([docs](https://code.claude.com/docs/en/agent-teams)) |
| `CLAUDE_CODE_NO_FLICKER` | Claude Code | `1` (enabled) | Fullscreen rendering (flicker-free display, flat memory usage, mouse support) is now the default; set to `0` to opt back into the classic renderer, or use `"tui": "fullscreen"` in `settings.json` ([docs](https://code.claude.com/docs/en/fullscreen)) |
| `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` | Claude Code | `0` (enabled) | Set to `1` to hide the skills and workflows bundled with Claude Code itself (e.g. `/init`, `/security-review`); plugin skills and this project's own `.claude/skills/` are unaffected. Equivalent to `"disableBundledSkills": true` in `settings.json` ([docs](https://code.claude.com/docs/en/settings)) |
| `BASH_DEFAULT_TIMEOUT_MS` | Claude Code | `120000` (2 min) | Default timeout for Bash commands. Raise it if your test suite regularly runs longer than two minutes, otherwise `uv run pytest` gets killed mid-run |
| `BASH_MAX_OUTPUT_LENGTH` | Claude Code | `30000` (max `150000`) | Characters of command output Claude reads back. Raise it when verbose `pytest -v` output gets truncated before the failure summary |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | Claude Code | `3` | How many layers of subagents can nest below the main conversation. Set `1` to turn nesting off ([docs](https://code.claude.com/docs/en/sub-agents)) |
| `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | Claude Code | `20` | How many subagents may run at once before `Agent` spawns start failing. Requires Claude Code v2.1.217+ ([docs](https://code.claude.com/docs/en/sub-agents)) |
| `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION` | Claude Code | `200` | WebSearch calls allowed per session, counted across the main conversation **and every subagent**, so parallel research fan-outs draw on the same budget. Accepts a positive whole number — the cap can be raised but not turned off; `/clear` resets the count. Requires v2.1.212+ ([docs](https://code.claude.com/docs/en/tools-reference)) |
| `CLAUDE_CODE_MCP_AUTO_BACKGROUND_MS` | Claude Code | `120000` (2 min) | How long a main-conversation MCP tool call may run before it moves to a background task instead of blocking the session. Set `0` to disable auto-backgrounding. Calls from subagents are never backgrounded. Requires v2.1.212+ ([docs](https://code.claude.com/docs/en/mcp)) |

### 4. Verify MCP servers

Run `/mcp` inside Claude Code to check that all servers are connected.

### 5. Install development tooling (optional)

The `pyproject.toml` declares [PEP 735 dependency groups](https://docs.astral.sh/uv/concepts/dependencies/#dependency-groups) for the tools this setup relies on:

```bash
# Core tooling (ruff, pytest, pytest-cov) — used by the auto-lint hook,
# the enforce-uv hook, and the verification flow. Installed by default:
uv sync

# Agent tooling (mypy, bandit, pip-audit, safety, vulture, autoflake) —
# only needed by on-demand agents (security-reviewer, refactor-cleaner,
# code-reviewer). Opt in when required:
uv sync --group agents
```

## Components

### CLAUDE.md (project root)

`CLAUDE.md` is the **project instructions file** that Claude Code reads automatically at the start of every conversation. It defines the coding standards, conventions, and constraints that Claude must follow when working on your project.

Think of it as a persistent system prompt scoped to your codebase. It's always loaded — no manual invocation needed.

Key characteristics:

- **Auto-loaded**: Claude reads it at startup, before any user message
- **Imports via `@path`**: use `@.claude/rules/testing.md` to pull in modular rules without bloating the main file
- **Keep under 200 lines**: long files waste context; extract details into rules
- **Project-scoped**: place in the project root for repo-wide instructions; nest in subdirectories for folder-specific overrides

This setup's `CLAUDE.md` contains project specs (OS, language, tools), naming conventions, file organization, common commands, and `@import` references to all rules.

> Full documentation: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)

### Rules (`.claude/rules/`)

Rules are **modular coding standards** that extend `CLAUDE.md` without inflating it. Each rule is a standalone Markdown file focused on a single topic (testing, security, API patterns, etc.), imported into `CLAUDE.md` via `@.claude/rules/<file>.md`.

Rules are loaded into Claude's context at session start alongside `CLAUDE.md`, so they act as persistent instructions — not invoked on demand like skills or agents.

Key characteristics:

- **Always in context**: rules are loaded at startup and apply to every interaction
- **Path-scoped** (optional): add `paths` in YAML frontmatter to activate a rule only for matching file patterns (e.g., `api-patterns.md` only for `src/api/**/*.py`)
- **One topic per file**: keeps each rule focused and easy to update independently
- **Referenced by agents**: agents point to rules instead of duplicating standards (e.g., "see `.claude/rules/security.md`")

> Full documentation: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)

| Rule | Scope | Description |
|------|-------|-------------|
| **api-patterns** | `src/api/**/*.py` | FastAPI routers, Pydantic models, dependency injection |
| **architecture** | global | Layered architecture, modularity, dependency flow |
| **compaction** | global | What to preserve during context compaction |
| **documentation** | global | README, docstrings, type annotations, changelog |
| **exception-handling** | global | Custom exception hierarchy, catch-at-boundary pattern |
| **git-workflow** | global | Conventional Commits, branch naming, PR conventions |
| **project-structure** | global | src layout, module conventions, pydantic-settings config |
| **python-idioms** | global | Data structure selection, generators, match/case, explicit kwargs, unpacking |
| **security** | global | Secrets management, input validation, injection prevention |
| **testing** | global | pytest structure, coverage targets, fixtures, markers |

### Hooks (`.claude/hooks/`)

Hooks are **deterministic guardrails** that run automatically before or after Claude uses a tool. Unlike rules (which are advisory — Claude _should_ follow them), hooks are enforced by the system — Claude _cannot_ bypass them.

Each hook is a shell script triggered by a specific event. `PreToolUse` hooks can block an action before it happens; `PostToolUse` hooks run after a tool completes (e.g., to auto-format code). Hook configuration lives in `.claude/settings.json`.

Key characteristics:

- **Deterministic**: hooks always execute — they don't depend on Claude's interpretation
- **Blocking**: `PreToolUse` hooks return a `hookSpecificOutput` object whose `permissionDecision` is one of `deny` (block), `allow` (auto-approve), `ask` (escalate to the user), or `defer` (fall back to the normal permission flow); they can also rewrite the tool call via `updatedInput`. Example: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`
- **Composable**: multiple hooks can run on the same event (e.g., enforce-uv + protect-main both run on Bash)
- **Conditional**: an `if` field (permission-rule syntax, e.g. `Bash(git *)`) scopes a hook to matching commands so it doesn't spawn a process on every tool call — `enforce-uv` and `protect-main` use this to skip non-Python/non-git commands
- **Dependency**: requires `jq` for JSON parsing of hook input

This setup hooks into `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, and `Stop`. Claude Code exposes **32 events** in total. Among the ones most useful to extend this setup:

- `PostToolBatch` — after a whole batch of parallel tool calls resolves (run linting once per batch instead of once per file)
- `PostToolUseFailure` — after a tool call fails, for reacting to errors rather than successes
- `SubagentStart` / `SubagentStop` — around each subagent's lifecycle
- `InstructionsLoaded` — when a `CLAUDE.md` or `.claude/rules/*.md` file is loaded into context
- `PermissionRequest` / `PermissionDenied` — when a call needs a permission decision, or auto mode denies it
- `SessionEnd`, `PreCompact` / `PostCompact`, `Notification`, `ConfigChange`, `FileChanged`

See the docs for the full list.

> Full documentation: [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)

| Hook | Event | Description |
|------|-------|-------------|
| **session-start** | `SessionStart` | Checks the uv environment (`.venv`, `uv.lock` freshness) and injects the status into the session context |
| **guard-secrets** | `UserPromptSubmit` | Blocks a prompt that looks like it contains a hardcoded secret (API keys, tokens, private keys) |
| **enforce-uv** | `PreToolUse` (Bash) | Auto-rewrites simple bare `python`/`pytest`/`ruff`/`mypy`/`bandit` calls to `uv run`; blocks `pip` and ambiguous cases with `uv add`/`uv sync` guidance |
| **protect-main** | `PreToolUse` (Bash) | Blocks `git push --force`, direct push to main/master, `git reset --hard`, broad `rm -rf` |
| **auto-lint** | `PostToolUse` (Edit\|Write) | Runs `ruff check --fix` and `ruff format` on Python files after every edit |
| **verify** | `Stop` | Runs `ruff check` + `pytest` when Claude finishes; on failure, blocks the stop and feeds the errors back so Claude keeps fixing |

### Permissions (`.claude/settings.json`)

Pre-configured permission rules in `.claude/settings.json` control what Claude can and cannot access.

**Allowed commands** — auto-approved without prompting:

| Pattern | Description |
|---------|-------------|
| `uv sync *`, `uv add *`, `uv remove *` | Dependency management |
| `uv run pytest *`, `uv run ruff *`, `uv run python *` | Test, lint, and run |

**Denied reads** — Claude is blocked from reading sensitive files:

| Pattern | Files protected |
|---------|-----------------|
| `.env`, `.env.{local,development,staging,production,test}`, `.envrc` | Environment variables (`.env.example` is allowed) |
| `secrets/**` | Secrets directory |
| `**/credentials*`, `**/secret*` | Credential and secret files |
| `**/*.pem`, `**/*.key`, `**/*.p12`, `**/*.pfx`, `**/*.jks` | Certificates and private keys |
| `**/*token*` | Token files |
| `~/.ssh/**`, `**/id_rsa*`, `**/id_ed25519*`, `**/id_ecdsa*`, `**/id_dsa*` | SSH keys |

These rules are enforced at the system level — Claude cannot bypass them regardless of the prompt. Customize by editing the `permissions` object in `.claude/settings.json`.

> Full documentation: [code.claude.com/docs/en/settings#excluding-sensitive-files](https://code.claude.com/docs/en/settings#excluding-sensitive-files)

**Fallback model** — `.claude/settings.json` also sets `fallbackModel`, a chain of up to three models (e.g. `["claude-sonnet-5", "claude-haiku-4-5-20251001"]`) that Claude Code switches to when the primary model is overloaded or unavailable, keeping the session going. Edit or remove the array to match your plan's model access.

**Default permission mode** — `permissions.defaultMode` is set explicitly to `"default"` (prompt on first use of each tool) so the behavior is visible and easy to change, rather than relying on the implicit default. Other values: `"plan"` (read-only, no modifications), `"acceptEdits"` (auto-accepts file edits), `"bypassPermissions"` (skips all prompts — isolated environments only), `"dontAsk"` (auto-denies unless pre-approved), `"auto"` (auto-approves with background safety checks).

> Since Claude Code v2.1.200 the `default` mode is **labeled "Manual"** in the CLI, the VS Code and JetBrains extensions, and the desktop app — look for "Manual", not "default", in the `Shift+Tab` mode cycle. The `"default"` value stays canonical and needs no migration; `"manual"` is accepted as an alias.

Two related settings are intentionally **not** set here, since they have no neutral value that preserves default behavior while being explicit — adding them would itself be a behavior change:

- `permissions.disableAutoMode: "disable"` — permanently removes `auto` from the `Shift+Tab` mode cycle; there's no value that means "keep auto mode available" other than omitting the key.
- `language: "italian"` (or any language name) — pins Claude's response language, voice dictation, and terminal tab title generation to that language; omitting it lets Claude follow the conversation's language.

> Full documentation: [code.claude.com/docs/en/settings](https://code.claude.com/docs/en/settings)

### Bash Sandbox (opt-in, not enabled here)

The permission rules above govern **Claude's tools**. The Bash sandbox is a different layer: it constrains what a shell command can touch *once it runs*, enforced by the operating system for the command and every child process it spawns. A `deny` rule stops the `Read` tool from opening `~/.ssh/id_rsa`; the sandbox stops a shell command from reading it.

In exchange for defining the boundary up front, Claude stops asking permission for each command — in auto-allow mode, anything that fits inside the sandbox just runs.

**This template does not enable it**, deliberately. The sandbox runs on macOS, Linux, and WSL2, but **not on native Windows**, and this setup is meant to work unchanged on all three. Enabling it in a checked-in `.claude/settings.json` would degrade to a startup warning for every Windows contributor. Turn it on per-machine instead: run `/sandbox` to see the panel, install status, and mode.

On macOS nothing needs installing (it uses Seatbelt). On Linux and WSL2 it needs `bubblewrap` (filesystem isolation) and `socat` (network relay).

A starting point for a uv-based Python project — add to your **user** settings (`~/.claude/settings.json`) so it follows you across projects without affecting Windows contributors:

```json
{
  "sandbox": {
    "enabled": true,
    "network": {
      "allowedDomains": [
        "pypi.org",
        "files.pythonhosted.org",
        "github.com",
        "*.githubusercontent.com"
      ]
    },
    "credentials": {
      "files": [
        { "path": "~/.aws/credentials", "mode": "deny" },
        { "path": "~/.ssh", "mode": "deny" }
      ],
      "envVars": [
        { "name": "POSTGRES_PASSWORD", "mode": "deny" }
      ]
    }
  }
}
```

The `allowedDomains` list covers `uv sync`, `uv add`, and `git` against GitHub. Any other host prompts once on first use, so the list only needs the traffic you don't want to be asked about. Sandboxed commands can write to the working directory and the session temp directory; widen that with `sandbox.filesystem.allowWrite` if a tool needs more.

Two things worth knowing before relying on it:

- **There is no built-in credential deny list.** Only the paths and variables you list under `credentials` are protected — the default read policy still allows `~/.aws` and `~/.ssh`. The block above is a starting point, not a complete one.
- **Sandbox failures can be retried outside the sandbox.** When a command fails on a sandbox restriction, Claude may retry it with `dangerouslyDisableSandbox`, which then goes through the normal permission flow. Set `"allowUnsandboxedCommands": false` to remove that escape hatch entirely.

> Full documentation: [code.claude.com/docs/en/sandboxing](https://code.claude.com/docs/en/sandboxing)

### Agents (`.claude/agents/`)

Agents are **specialized AI subagents** that run in their own context window with a custom system prompt, specific tool access, and independent permissions. When Claude encounters a task that matches an agent's description, it **automatically delegates** to that agent, which works independently and returns results.

Each agent is a Markdown file with YAML frontmatter (configuration) and a body (system prompt). Agents help preserve the main conversation context by isolating heavy tasks, and can enforce constraints like read-only access or specific tool sets.

Key characteristics:

- **Automatic delegation**: Claude uses the agent's `description` to decide when to delegate
- **Isolated context**: each agent runs in its own context window, keeping verbose output out of the main conversation
- **Configurable tools and model**: agents can restrict tool access and use a different model (e.g., Haiku for speed)
- **Nesting**: subagents can spawn their own subagents, up to 3 layers below the main conversation by default; at the limit Claude Code withholds the `Agent` tool so the subagent does the work itself. Change the limit with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
- **Background by default**: subagents now run in the background while you keep working, and notify on completion or when they need input

> Full documentation: [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)

| Agent | Description |
|-------|-------------|
| **architect** | System design, ADRs, trade-off analysis, scalability planning |
| **code-architect** | Implementation blueprints: file plans, data flow, build sequence |
| **code-explorer** | Codebase tracing: execution paths, architecture mapping, dependency analysis |
| **code-reviewer** | Code quality, Python patterns, concurrency, FastAPI/Django/Flask checks |
| **comment-analyzer** | Code comment accuracy, completeness, and comment rot detection |
| **database-reviewer** | PostgreSQL schema, query optimization, and migration review |
| **planner** | Task decomposition and implementation planning |
| **pr-test-analyzer** | Test coverage quality: behavioral gaps, critical paths, edge cases |
| **refactor-cleaner** | Dead code detection, refactoring (vulture, ruff) |
| **security-reviewer** | Security audit (bandit, safety, pip-audit, OWASP Top 10) |
| **silent-failure-hunter** | Error handling audit: silent failures, catch blocks, fallback behavior |
| **tdd-guide** | Test-driven development with pytest |
| **type-design-analyzer** | Type design quality: encapsulation, invariants, enforcement ratings |

### Skills (`.claude/skills/`)

Skills **extend what Claude can do**. Each skill is a directory containing a `SKILL.md` file (with optional supporting files like templates, examples, or scripts). Claude loads skills automatically when relevant to the conversation, or you can invoke them directly with `/skill-name`.

Skills serve two purposes:

- **Reference content**: conventions, patterns, domain knowledge that Claude applies to your work (loaded inline)
- **Task content**: step-by-step workflows for specific actions like deployments or code generation

Key characteristics:

- **Auto-discovery**: Claude reads skill descriptions and loads them when relevant
- **Invocation control**: `disable-model-invocation: true` makes a skill user-only; `user-invocable: false` makes it Claude-only
- **Arguments**: skills accept `$ARGUMENTS` from the user (e.g., `/fix-issue 123`)
- **Subagent execution**: skills with `context: fork` run in an isolated subagent
- **Supporting files**: a skill directory can include templates, examples, and scripts alongside `SKILL.md`

> Full documentation: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)

Ten of the skills below are **vendored from [anthropics/skills](https://github.com/anthropics/skills)** rather than written for this template: `claude-api`, `doc-coauthoring`, `docx`, `frontend-design`, `mcp-builder`, `pdf`, `pptx`, `skill-creator`, `webapp-testing`, `xlsx`. They are copies, so they don't update themselves — re-sync them from upstream periodically, especially `claude-api`, which pins the model IDs Claude will reach for. Last synced from upstream `f17010c` (2026-08-13).

| Skill | Description |
|-------|-------------|
| **api-design** | REST API design: resource naming, status codes, pagination, versioning |
| **claude-api** | Claude API and Anthropic SDK reference: model IDs and pricing, streaming, tool use, prompt caching, token counting, Managed Agents, model migration |
| **claude-automation-recommender** | Analyze codebases and recommend Claude Code automations (hooks, skills, MCP servers) |
| **claude-md-improver** | Audit and improve CLAUDE.md files: quality scoring, targeted updates |
| **database-migrations** | Safe zero-downtime migrations, reversible patterns (SQLAlchemy, Django, golang-migrate) |
| **deployment-patterns** | CI/CD pipelines, rolling/blue-green deployments, health checks, production readiness |
| **django-patterns** | Django architecture, DRF, ORM best practices, caching, signals, middleware |
| **django-security** | Django security: authentication, CSRF/XSS prevention, secure configuration |
| **django-tdd** | TDD with pytest-django, factory_boy, model/view/serializer testing |
| **django-verification** | Django pre-deployment verification: migrations, tests, security scans |
| **doc-coauthoring** | Structured documentation co-authoring workflow |
| **docker-patterns** | Docker/Compose: multi-container orchestration, networking, security hardening |
| **docx** | Word document and `.dotx` template creation and manipulation |
| **frontend-design** | Visual design direction for new or reshaped UI: aesthetics, typography, avoiding templated defaults |
| **mcp-builder** | Guide for creating MCP servers |
| **pdf** | PDF reading, merging, splitting, OCR |
| **playground** | Interactive HTML playgrounds: visual controls, live preview, prompt output |
| **postgres-patterns** | PostgreSQL query optimization, schema design, indexing, RLS, connection pooling |
| **pptx** | PowerPoint presentation and `.potx` template creation |
| **skill-creator** | Create and optimize skills, run evals, benchmark triggering accuracy |
| **webapp-testing** | Web app testing with Playwright |
| **xlsx** | Spreadsheet creation and manipulation |

### Commands (`.claude/commands/`)

Commands are **the legacy format for skills**. A file at `.claude/commands/review.md` and a skill at `.claude/skills/review/SKILL.md` both create `/review` and work identically. Existing command files continue to work and support the same frontmatter as skills.

Skills are the recommended format because they support additional features (supporting files directory, auto-discovery by Claude). Commands are kept for simplicity when a single `.md` file is sufficient.

> Full documentation: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)

| Command | Description |
|---------|-------------|
| `/build-fix` | Incremental build/type error fixing with guardrails |
| `/clean-gone` | Clean up stale local branches marked as [gone] and their worktrees |
| `/commit` | Stage and create a git commit with contextual message |
| `/commit-push-pr` | One-command workflow: branch → commit → push → PR creation |
| `/feature-dev` | Guided 7-phase feature development with codebase exploration and architecture design |
| `/notebook-review` | Review Jupyter notebooks |
| `/orchestrate` | Multi-agent workflow: planner → tdd-guide → code-reviewer → security-reviewer |
| `/review-pr` | Interactive PR review with formal GitHub decision (approve/request changes/comment) |
| `/revise-claude-md` | Capture session learnings and update CLAUDE.md |
| `/test-coverage` | Analyze coverage gaps, generate missing tests for 80%+ target |

### MCP Servers (`.mcp.json`)

MCP (Model Context Protocol) servers **extend Claude Code with external tool integrations**. They run as local processes that Claude communicates with via stdio, providing access to databases, browsers, APIs, and other services.

The `.mcp.json` file in the project root defines which servers are available. Each server declaration specifies a command to launch and its arguments. Environment variables are expanded at runtime using `${VAR:-default}` syntax.

> Full documentation: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp)

| Server | Description | Recommended |
|--------|-------------|-------------|
| **context7** | Up-to-date library documentation lookup | Always |
| **playwright** | Browser automation, testing, and web scraping | If testing web apps or scraping |
| **postgres** | PostgreSQL database interaction | If using PostgreSQL |
| **docker** | Docker container management | If using Docker |

> **context7** is recommended for all projects — it gives Claude access to current library docs, reducing hallucinated APIs and outdated patterns. The other servers are situational: keep or remove them from `.mcp.json` based on your project's stack.

### Status Line (`.claude/statusline.py`)

A persistent status bar at the bottom of Claude Code that displays session info at a glance. It's **pre-configured** in `.claude/settings.json` and works automatically — no setup needed.

The status line shows three rows:

| Row | Content |
|-----|---------|
| **1** | Model name, current directory, git branch with staged/modified counts (color-coded) |
| **2** | Context window progress bar (green/yellow/red), context %, session cost, elapsed time |
| **3** | Rate limit usage bars for 5-hour and 7-day windows (Pro/Max only, hidden until first API response) |

The script is written in Python and works cross-platform: Windows, macOS, and Linux. Git operations are cached for 5 seconds to avoid lag on large repositories.

> Full documentation: [code.claude.com/docs/en/statusline](https://code.claude.com/docs/en/statusline)

## Contributing

Contributions are welcome! If you have ideas for new agents, skills, rules, or improvements to the existing setup:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-idea`)
3. Make your changes
4. Submit a Pull Request with a clear description of what you added or changed

For bug reports or suggestions, open an [issue](https://github.com/skateddu/claude-code-python-setup/issues).

## References

This project builds on top of the official Claude Code documentation and tooling by Anthropic:

- [Claude Code Documentation](https://code.claude.com/docs): setup guides, CLAUDE.md reference, skills, agents, MCP configuration
- [Anthropic GitHub](https://github.com/anthropics): official repositories and examples
- [Model Context Protocol](https://modelcontextprotocol.io/): open standard for LLM-tool integrations
