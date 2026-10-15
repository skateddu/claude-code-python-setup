---
name: django-verification
description: Run the full Django verification loop — environment check, mypy and ruff checks, migration safety, pytest with coverage targets, pip-audit and bandit security scans, settings and logging review, and diff review — producing a phased pass/fail report before release or PR. Use when preparing a Django pull request, validating migrations or coverage, or running pre-deploy readiness checks.
metadata:
  origin: ECC
---

# Django Verification Loop

Run before PRs, after major changes, and pre-deploy to ensure Django application quality and security.

## When to Activate

- Before opening a pull request for a Django project
- After major model changes, migration updates, or dependency upgrades
- Pre-deployment verification for staging or production
- Running full environment → lint → test → security → deploy readiness pipeline
- Validating migration safety and test coverage

## Phase 1: Environment Check

```bash
# Verify Python version
uv run python --version  # Should match requires-python in pyproject.toml

# Check the environment is in sync with uv.lock
uv sync --locked
uv pip list --outdated

# Verify environment variables
uv run python -c "import os; print('DJANGO_SECRET_KEY set' if os.environ.get('DJANGO_SECRET_KEY') else 'MISSING: DJANGO_SECRET_KEY')"
```

If environment is misconfigured, stop and fix.

## Phase 2: Code Quality & Formatting

```bash
# Type checking (mypy is in the opt-in `agents` group: uv sync --group agents)
uv run mypy . --config-file pyproject.toml

# Linting with ruff (import sorting included via the "I" rules)
uv run ruff check . --fix

# Formatting with ruff
uv run ruff format --check .
uv run ruff format .  # Auto-fix

# Django-specific checks
uv run python manage.py check --deploy
```

Common issues:
- Missing type hints on public functions
- PEP 8 formatting violations
- Unsorted imports
- Debug settings left in production configuration

## Phase 3: Migrations

```bash
# Check for unapplied migrations
uv run python manage.py showmigrations

# Create missing migrations
uv run python manage.py makemigrations --check

# Dry-run migration application
uv run python manage.py migrate --plan

# Apply migrations (test environment)
uv run python manage.py migrate

# Check for migration conflicts
uv run python manage.py makemigrations --merge  # Only if conflicts exist
```

Report:
- Number of pending migrations
- Any migration conflicts
- Model changes without migrations

## Phase 4: Tests + Coverage

```bash
# Run all tests with pytest
uv run pytest --cov=apps --cov-report=html --cov-report=term-missing --reuse-db

# Run specific app tests
uv run pytest apps/users/tests/

# Run with markers
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest -m integration  # Only integration tests

# Coverage report
open htmlcov/index.html
```

Report:
- Total tests: X passed, Y failed, Z skipped
- Overall coverage: XX%
- Per-app coverage breakdown

Coverage targets:

| Component | Target |
|-----------|--------|
| Models | 90%+ |
| Serializers | 85%+ |
| Views | 80%+ |
| Services | 90%+ |
| Overall | 80%+ |

## Phase 5: Security Scan

```bash
# Dependency vulnerabilities (pip-audit needs no account; `safety check` is
# deprecated and its replacement `safety scan` requires a Safety login)
uv run pip-audit

# Django security checks
uv run python manage.py check --deploy

# Bandit security linter
uv run bandit -r . -f json -o bandit-report.json

# Secret scanning (if gitleaks is installed)
gitleaks detect --source . --verbose

# DEBUG status, read through Django so the settings module is loaded
uv run python manage.py shell -c "from django.conf import settings; print('DEBUG =', settings.DEBUG)"
```

Report:
- Vulnerable dependencies found
- Security configuration issues
- Hardcoded secrets detected
- DEBUG mode status (should be False in production)

## Phase 6: Django Management Commands

```bash
# Check for model issues
uv run python manage.py check

# Collect static files
uv run python manage.py collectstatic --noinput --clear

# Database integrity
uv run python manage.py check --database default

# Cache verification (if using Redis)
uv run python manage.py shell -c "from django.core.cache import cache; cache.set('verification', 'ok', 10); print(cache.get('verification'))"
```

## Phase 7: Performance Checks

```bash
# Django Debug Toolbar output (check for N+1 queries)
# Run in dev mode with DEBUG=True and access a page
# Look for duplicate queries in SQL panel

# Query count analysis (debugsqlshell is provided by django-debug-toolbar)
uv run python manage.py debugsqlshell

# List existing indexes (PostgreSQL)
uv run python manage.py shell << EOF
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename")
    print(cursor.fetchall())
EOF
```

Report:
- Number of queries per page (should be < 50 for typical pages)
- Missing database indexes
- Duplicate queries detected

## Phase 8: Static Assets

```bash
# Check for npm dependencies (if using npm)
npm audit

# Build static files (if using webpack/vite)
npm run build

# Verify static files
ls -la staticfiles/
uv run python manage.py findstatic css/style.css
```

## Phase 9: Configuration Review

```bash
# Run in the Django shell to verify settings
uv run python manage.py shell << EOF
from django.conf import settings
import os

# Critical checks
checks = {
    'DEBUG is False': not settings.DEBUG,
    'SECRET_KEY set': bool(settings.SECRET_KEY and len(settings.SECRET_KEY) > 30),
    'ALLOWED_HOSTS set': len(settings.ALLOWED_HOSTS) > 0,
    'HTTPS enabled': getattr(settings, 'SECURE_SSL_REDIRECT', False),
    'HSTS enabled': getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0,
    'Database configured': settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3',
}

for check, result in checks.items():
    status = '✓' if result else '✗'
    print(f"{status} {check}")
EOF
```

## Phase 10: Logging Configuration

```bash
# Test logging output
uv run python manage.py shell << EOF
import logging
logger = logging.getLogger('django')
logger.warning('Test warning message')
logger.error('Test error message')
EOF

# Check the latest log entries (if configured); not `tail -f`, which never returns
tail -n 50 /var/log/django/django.log
```

## Phase 11: API Documentation (if DRF)

```bash
# Generate schema
uv run python manage.py generateschema --format openapi-json > schema.json

# Validate schema
# Check if schema.json is valid JSON
uv run python -c "import json; json.load(open('schema.json'))"

# Access Swagger UI (if using drf-yasg)
# Visit http://localhost:8000/swagger/ in browser
```

## Phase 12: Diff Review

```bash
# Show diff statistics
git diff --stat

# Show actual changes
git diff

# Show changed files
git diff --name-only

# Check for common issues
git diff | grep -i "todo\|fixme\|hack\|xxx"
git diff | grep "print("  # Debug statements
git diff | grep "DEBUG = True"  # Debug mode
git diff | grep "import pdb"  # Debugger
```

Checklist:
- No debugging statements (print, pdb, breakpoint())
- No TODO/FIXME comments in critical code
- No hardcoded secrets or credentials
- Database migrations included for model changes
- Configuration changes documented
- Error handling present for external calls
- Transaction management where needed

## Output Template

```
DJANGO VERIFICATION REPORT
==========================

Phase 1: Environment Check
  ✓ Python 3.11.5
  ✓ Environment in sync with uv.lock
  ✓ All environment variables set

Phase 2: Code Quality
  ✓ mypy: No type errors
  ✗ ruff: 3 issues found (auto-fixed)
  ✓ ruff format: No formatting issues
  ✓ manage.py check: No issues

Phase 3: Migrations
  ✓ No unapplied migrations
  ✓ No migration conflicts
  ✓ All models have migrations

Phase 4: Tests + Coverage
  Tests: 247 passed, 0 failed, 5 skipped
  Coverage:
    Overall: 87%
    users: 92%
    products: 89%
    orders: 85%
    payments: 91%

Phase 5: Security Scan
  ✗ pip-audit: 2 vulnerabilities found (fix required)
  ✓ bandit: No security issues
  ✓ No secrets detected
  ✓ DEBUG = False

Phase 6: Django Commands
  ✓ collectstatic completed
  ✓ Database integrity OK
  ✓ Cache backend reachable

Phase 7: Performance
  ✓ No N+1 queries detected
  ✓ Database indexes configured
  ✓ Query count acceptable

Phase 8: Static Assets
  ✓ npm audit: No vulnerabilities
  ✓ Assets built successfully
  ✓ Static files collected

Phase 9: Configuration
  ✓ DEBUG = False
  ✓ SECRET_KEY configured
  ✓ ALLOWED_HOSTS set
  ✓ HTTPS enabled
  ✓ HSTS enabled
  ✓ Database configured

Phase 10: Logging
  ✓ Logging configured
  ✓ Log files writable

Phase 11: API Documentation
  ✓ Schema generated
  ✓ Swagger UI accessible

Phase 12: Diff Review
  Files changed: 12
  +450, -120 lines
  ✓ No debug statements
  ✓ No hardcoded secrets
  ✓ Migrations included

RECOMMENDATION: WARNING: Fix pip-audit vulnerabilities before deploying

NEXT STEPS:
1. Update vulnerable dependencies
2. Re-run security scan
3. Deploy to staging for final testing
```

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] No security vulnerabilities
- [ ] No unapplied migrations
- [ ] DEBUG = False in production settings
- [ ] SECRET_KEY properly configured
- [ ] ALLOWED_HOSTS set correctly
- [ ] Database backups enabled
- [ ] Static files collected and served
- [ ] Logging configured and working
- [ ] Error monitoring (Sentry, etc.) configured
- [ ] CDN configured (if applicable)
- [ ] Redis/cache backend configured
- [ ] Celery workers running (if applicable)
- [ ] HTTPS/SSL configured
- [ ] Environment variables documented

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/django-verification.yml
name: Django Verification

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v7

      - name: Set up uv
        uses: astral-sh/setup-uv@v10.3.0
        with:
          enable-cache: true

      - name: Install dependencies
        # Installs the default `dev` group plus the opt-in `agents` group (mypy, bandit, pip-audit)
        run: uv sync --locked --group agents

      - name: Code quality checks
        run: |
          uv run ruff check .
          uv run ruff format --check .
          uv run mypy .

      - name: Security scan
        run: |
          uv run bandit -r . -f json -o bandit-report.json
          uv run pip-audit

      - name: Run tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/test
          DJANGO_SECRET_KEY: test-secret-key
        run: |
          uv run pytest --cov=apps --cov-report=xml --cov-report=term-missing

      - name: Upload coverage
        uses: codecov/codecov-action@v7
```

## Quick Reference

| Check | Command |
|-------|---------|
| Environment | `uv sync --locked` |
| Type checking | `uv run mypy .` |
| Linting | `uv run ruff check .` |
| Formatting | `uv run ruff format --check .` |
| Migrations | `uv run python manage.py makemigrations --check` |
| Tests | `uv run pytest --cov=apps` |
| Security | `uv run pip-audit && uv run bandit -r .` |
| Django check | `uv run python manage.py check --deploy` |
| Collectstatic | `uv run python manage.py collectstatic --noinput` |
| Diff stats | `git diff --stat` |

Remember: Automated verification catches common issues but doesn't replace manual code review and testing in staging environment.
