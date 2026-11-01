"""The Read deny rules in `settings.json` cover credential files, not source code.

A deny rule on reads also refuses writes, so a rule written as a word in the
file name (`*token*`, `secret*`, `credentials*`) locked Claude out of ordinary
modules such as `auth/tokens.py` or `secret_manager.py`, and of this
template's own `token-counting.md`. The rules now name credential files by
their shape. Matching here follows the rules' two forms: `./**/<name glob>`
against the file name at any depth, and an exact or `/**` path otherwise.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import PurePosixPath

import pytest

from tests.hook_harness import SETTINGS_PATH

PROJECT_PREFIX = "Read(./"
ANY_DEPTH_PREFIX = "Read(./**/"

CREDENTIAL_FILES = [
    ".env",
    ".env.production",
    "secrets/prod.yaml",
    "config/secrets.toml",
    "deploy/secrets.yaml",
    "app/api.secret",
    "certs/server.pem",
    "certs/server.key",
    "deploy/id_rsa",
    "config/token.json",
    "auth/service.token",
    "gcp/credentials.json",
    "aws/credentials",
    ".pypirc",
    ".netrc",
]

SOURCE_AND_DOCS = [
    ".env.example",
    "src/app/auth/tokens.py",
    "src/app/tokenizer.py",
    "src/app/services/token_service.py",
    "tests/test_tokens.py",
    "src/app/secrets.py",
    "src/app/secret_manager.py",
    "config/secrets.example.toml",
    "src/app/credentials.py",
    "docs/credentials-setup.md",
    ".claude/skills/claude-api/shared/token-counting.md",
]

HOME_CREDENTIALS = [
    "Read(~/.ssh/**)",
    "Read(~/.pypirc)",
    "Read(~/.netrc)",
    "Read(~/.aws/credentials)",
]


def _deny_rules() -> list[str]:
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    return settings["permissions"]["deny"]


def _is_denied(path: str) -> bool:
    """Whether a project-relative `path` matches any project Read deny rule."""
    for rule in _deny_rules():
        if rule.startswith(ANY_DEPTH_PREFIX):
            if fnmatch.fnmatchcase(PurePosixPath(path).name, rule[len(ANY_DEPTH_PREFIX) : -1]):
                return True
        elif rule.startswith(PROJECT_PREFIX):
            pattern = rule[len(PROJECT_PREFIX) : -1]
            if pattern.endswith("/**"):
                if path.startswith(pattern[: -len("**")]):
                    return True
            elif path == pattern:
                return True
    return False


@pytest.mark.parametrize("path", CREDENTIAL_FILES)
def test_deny_rules_cover_credential_file(path: str) -> None:
    assert _is_denied(path), f"{path} holds credentials but is readable"


@pytest.mark.parametrize("path", SOURCE_AND_DOCS)
def test_deny_rules_leave_source_and_docs_readable(path: str) -> None:
    assert not _is_denied(path), f"{path} is ordinary content but is denied"


@pytest.mark.parametrize("rule", HOME_CREDENTIALS)
def test_deny_rules_cover_home_credentials(rule: str) -> None:
    assert rule in _deny_rules()
