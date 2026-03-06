# Claude Code Python Setup

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

### MCP Server Dependencies

The included MCP servers require additional tools. Install only what you need:

| Dependency | Required by | Install |
|-----------|-------------|---------|
| **Node.js 18+** | context7, playwright | [nodejs.org](https://nodejs.org/) |
| **Python >= 3.10 + uv** | postgres, docker | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| **Docker** | docker | [docker.com](https://www.docker.com/get-started/) |
| **PostgreSQL** | postgres | Running instance (local or remote) |

> `npx` comes with Node.js. `uvx` comes with uv. No additional installs needed beyond the base tools.

## Project Structure

```
claude-code-python-setup/
├── .claude/
│   ├── agents/              # Specialized subagents
│   │   ├── architect.md
│   │   ├── code-reviewer.md
│   │   ├── database-reviewer.md
│   │   ├── planner.md
│   │   ├── refactor-cleaner.md
│   │   ├── security-reviewer.md
│   │   └── tdd-guide.md
│   ├── commands/            # Slash commands (/command-name)
│   │   ├── build-fix.md
│   │   ├── notebook-review.md
│   │   ├── orchestrate.md
│   │   ├── review-pr.md
│   │   ├── review-pr-ci.md
│   │   └── test-coverage.md
│   ├── rules/               # Modular coding standards
│   │   ├── api-patterns.md  # FastAPI/Pydantic (path-scoped)
│   │   ├── architecture.md
│   │   ├── documentation.md
│   │   ├── exception-handling.md
│   │   ├── git-workflow.md
│   │   ├── project-structure.md
│   │   ├── security.md
│   │   └── testing.md
│   └── skills/              # Reference docs and scripts
│       ├── api-design/
│       ├── canvas-design/
│       ├── claude-api/
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
│       ├── postgres-patterns/
│       ├── pptx/
│       ├── skill-creator/
│       ├── slack-gif-creator/
│       ├── theme-factory/
│       ├── webapp-testing/
│       └── xlsx/
├── mcp_config/
│   ├── linux_mac.mcp.json   # MCP server config (Linux/Mac)
│   └── windows.mcp.json     # MCP server config (Windows)
├── .env.example             # Environment variables template
├── .gitignore
├── .python-version          # Python version pin for uv
├── CLAUDE.md                # Project instructions (< 200 lines, imports rules)
├── LICENSE                  # MIT License
├── pyproject.toml           # Project metadata, ruff and pytest config
└── README.md
```

## Setup

### 1. Copy the `.claude` folder

Copy the `.claude/` directory and `CLAUDE.md` into the root of your project.

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

The PostgreSQL MCP server uses environment variables for connection parameters. These must be **system environment variables** (Claude Code does not read `.env` files).

```bash
# Linux / Mac — add to ~/.bashrc or ~/.zshrc
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=mydb
```

```powershell
# Windows — via setx or System Properties > Environment Variables
setx POSTGRES_USER myuser
setx POSTGRES_PASSWORD mypassword
setx POSTGRES_HOST localhost
setx POSTGRES_PORT 5432
setx POSTGRES_DB mydb
```

Default values are used when variables are not set (see `.env.example` for reference).

### 4. Verify MCP servers

Run `/mcp` inside Claude Code to check that all servers are connected.

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
| **documentation** | global | README, docstrings, type annotations, changelog |
| **exception-handling** | global | Custom exception hierarchy, catch-at-boundary pattern |
| **git-workflow** | global | Conventional Commits, branch naming, PR conventions |
| **project-structure** | global | src layout, module conventions, pydantic-settings config |
| **security** | global | Secrets management, input validation, injection prevention |
| **testing** | global | pytest structure, coverage targets, fixtures, markers |

### Agents (`.claude/agents/`)

Agents are **specialized AI subagents** that run in their own context window with a custom system prompt, specific tool access, and independent permissions. When Claude encounters a task that matches an agent's description, it **automatically delegates** to that agent, which works independently and returns results.

Each agent is a Markdown file with YAML frontmatter (configuration) and a body (system prompt). Agents help preserve the main conversation context by isolating heavy tasks, and can enforce constraints like read-only access or specific tool sets.

Key characteristics:
- **Automatic delegation**: Claude uses the agent's `description` to decide when to delegate
- **Isolated context**: each agent runs in its own context window, keeping verbose output out of the main conversation
- **Configurable tools and model**: agents can restrict tool access and use a different model (e.g., Haiku for speed)
- **Cannot nest**: subagents cannot spawn other subagents

> Full documentation: [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)

| Agent | Description |
|-------|-------------|
| **architect** | System design, ADRs, trade-off analysis, scalability planning |
| **code-reviewer** | Code quality, Python patterns, concurrency, FastAPI/Django/Flask checks |
| **database-reviewer** | PostgreSQL schema, query optimization, and migration review |
| **planner** | Task decomposition and implementation planning |
| **refactor-cleaner** | Dead code detection, refactoring (vulture, ruff) |
| **security-reviewer** | Security audit (bandit, safety, pip-audit, OWASP Top 10) |
| **tdd-guide** | Test-driven development with pytest |

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

| Skill | Description |
|-------|-------------|
| **api-design** | REST API design: resource naming, status codes, pagination, versioning |
| **canvas-design** | Visual art and design in .png/.pdf |
| **claude-api** | Claude API and Anthropic SDK reference |
| **database-migrations** | Safe zero-downtime migrations, reversible patterns (SQLAlchemy, Django, golang-migrate) |
| **deployment-patterns** | CI/CD pipelines, rolling/blue-green deployments, health checks, production readiness |
| **django-patterns** | Django architecture, DRF, ORM best practices, caching, signals, middleware |
| **django-security** | Django security: authentication, CSRF/XSS prevention, secure configuration |
| **django-tdd** | TDD with pytest-django, factory_boy, model/view/serializer testing |
| **django-verification** | Django pre-deployment verification: migrations, tests, security scans |
| **doc-coauthoring** | Structured documentation co-authoring workflow |
| **docker-patterns** | Docker/Compose: multi-container orchestration, networking, security hardening |
| **docx** | Word document creation and manipulation |
| **frontend-design** | Production-grade frontend interfaces (Django templates) |
| **mcp-builder** | Guide for creating MCP servers |
| **pdf** | PDF reading, merging, splitting, OCR |
| **postgres-patterns** | PostgreSQL query optimization, schema design, indexing, RLS, connection pooling |
| **pptx** | PowerPoint presentation creation |
| **skill-creator** | Create and optimize new skills |
| **slack-gif-creator** | Animated GIFs for Slack |
| **theme-factory** | Theming toolkit for artifacts |
| **webapp-testing** | Web app testing with Playwright |
| **xlsx** | Spreadsheet creation and manipulation |

### Commands (`.claude/commands/`)

Commands are **the legacy format for skills**. A file at `.claude/commands/review.md` and a skill at `.claude/skills/review/SKILL.md` both create `/review` and work identically. Existing command files continue to work and support the same frontmatter as skills.

Skills are the recommended format because they support additional features (supporting files directory, auto-discovery by Claude). Commands are kept for simplicity when a single `.md` file is sufficient.

> Full documentation: [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)

| Command | Description |
|---------|-------------|
| `/build-fix` | Incremental build/type error fixing with guardrails |
| `/notebook-review` | Review Jupyter notebooks |
| `/orchestrate` | Multi-agent workflow: planner → tdd → code-review → security |
| `/review-pr` | Review an open pull request |
| `/review-pr-ci` | Review a PR and post to GitHub (CI) |
| `/test-coverage` | Analyze coverage gaps, generate missing tests for 80%+ target |

### MCP Servers (`.mcp.json`)

MCP (Model Context Protocol) servers **extend Claude Code with external tool integrations**. They run as local processes that Claude communicates with via stdio, providing access to databases, browsers, APIs, and other services.

The `.mcp.json` file in the project root defines which servers are available. Each server declaration specifies a command to launch and its arguments. Environment variables are expanded at runtime using `${VAR:-default}` syntax.

> Full documentation: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp)

| Server | Description |
|--------|-------------|
| **context7** | Up-to-date library documentation lookup |
| **playwright** | Browser automation and testing |
| **postgres** | PostgreSQL database interaction |
| **docker** | Docker container management |

## Contributing

Contributions are welcome! If you have ideas for new agents, skills, rules, or improvements to the existing setup:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-idea`)
3. Make your changes
4. Submit a Pull Request with a clear description of what you added or changed

For bug reports or suggestions, open an [issue](https://github.com/skateddu/claude-code-python-setup/issues).

## Acknowledgments

This project builds on top of the official Claude Code documentation and tooling by Anthropic:

- [Claude Code Documentation](https://code.claude.com/docs) — setup guides, CLAUDE.md reference, skills, agents, MCP configuration
- [Anthropic GitHub](https://github.com/anthropics) — official repositories and examples
- [Model Context Protocol](https://modelcontextprotocol.io/) — open standard for LLM-tool integrations
