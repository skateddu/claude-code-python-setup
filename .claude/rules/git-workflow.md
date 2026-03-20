# Git Workflow

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
