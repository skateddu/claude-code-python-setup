# Security

## Secrets and Configuration

- Never hardcode secrets, API keys, passwords, or tokens in source code
- Use environment variables or `.env` files (loaded via pydantic-settings or python-dotenv)
- Keep `.env` in `.gitignore`; provide `.env.example` with placeholder values
- Use different secrets per environment (dev, staging, production)

## Input Validation

- Validate all external input at system boundaries (API endpoints, CLI arguments, file uploads)
- Use Pydantic models for request validation in FastAPI
- Sanitize user input before using in file paths, shell commands, or database queries
- Set explicit size limits on uploaded files and request bodies

## Injection Prevention

- SQL: always use parameterized queries or ORM methods, never f-strings or `.format()`
- Shell: avoid `subprocess.run(shell=True)`; pass arguments as a list
- Never use `eval()`, `exec()`, or `pickle.loads()` on untrusted input
- Template injection: use auto-escaping in Jinja2/Django templates

## Dependencies

- Audit dependencies periodically: `uv run pip-audit`
- Pin all dependency versions in `uv.lock`
- Review new dependencies before adding: check maintenance status, license, known vulnerabilities

## Authentication and Authorization

- Hash passwords with bcrypt or argon2, never store plaintext
- Use constant-time comparison for secrets (`hmac.compare_digest`)
- Validate JWT tokens server-side, check expiration and issuer
- Apply least-privilege: restrict access at the route/endpoint level
