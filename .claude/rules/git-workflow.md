# Git Workflow

## Branching Strategy

Follow **GitHub Flow**: a single stable branch (`main`) with short-lived feature branches.

- `main` is always deployable — never push broken code directly to it
- Every non-trivial change goes through a dedicated branch and PR
- Keep branches short-lived: merge or close within days, not weeks
- Delete branches after merge

## Proactive Proposals

Never create branches, commits, or push autonomously. Always **propose** git operations to the user, who accepts or rejects.

- If the working directory is not a git repository, propose `git init` with a `.gitignore` appropriate to the project stack
- Before starting any non-trivial change (feat, fix, refactor, test), propose creating a dedicated branch from `main`
- After completing a logical unit of work, propose a commit with a draft message
- After one or more commits, propose push and PR creation when appropriate

### Direct Commit on Main

Skip the branch proposal only for minimal, low-risk changes:

- Typo fixes in documentation or comments
- Single-line config adjustments (e.g., version bump in `pyproject.toml`)
- Updates to `CHANGELOG.md`, `README.md`, or other docs-only changes

Even for these, still propose the commit — never commit silently.

## Commit Messages

Use Conventional Commits format:

```
<type>(<scope>): <short description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `perf`, `style`

- Subject line: imperative mood, lowercase, no period, max 72 characters
- Body: explain **why**, not what (the diff shows what)
- Reference issue numbers when applicable: `fixes #42`, `closes #15`

## Branch Naming

```
feature/<short-description>    # New functionality
fix/<short-description>        # Bug fixes
refactor/<short-description>   # Code restructuring
chore/<short-description>      # Maintenance, deps, config
docs/<short-description>       # Documentation only
```

- Use kebab-case: `feature/user-authentication`, not `feature/userAuthentication`
- Keep branch names short and descriptive

## Pull Requests

- One logical change per PR (don't mix features with refactoring)
- PR title follows the same Conventional Commits format as commit messages
- Include a brief description of what and why
- Ensure CI passes before requesting review
- Delete branch after merge
