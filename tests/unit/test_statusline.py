"""Tests for the status line script and the command `settings.json` runs it with."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import pytest

from tests.hook_harness import REPO_ROOT

STATUSLINE_SCRIPT = REPO_ROOT / ".claude" / "statusline.py"
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
GREEN = "\033[32m"
YELLOW = "\033[33m"


def _session_line(payload: dict[str, Any]) -> str:
    """Run the status line against `payload` and return its second line."""
    completed = subprocess.run(
        [sys.executable, str(STATUSLINE_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
    return completed.stdout.splitlines()[1]


@pytest.mark.parametrize(
    ("prompt_cache", "expected_segment"),
    [
        ({"warm": True, "hit_ratio": 0.91}, f"cache {GREEN}91%"),
        ({"warm": False, "hit_ratio": 0.4}, f"cache {YELLOW}40%"),
    ],
    ids=["warm-cache-green", "cold-cache-yellow"],
)
def test_statusline_with_hit_ratio_shows_colored_cache_percentage(
    prompt_cache: dict[str, Any], expected_segment: str
) -> None:
    session_line = _session_line(payload={"prompt_cache": prompt_cache})

    assert expected_segment in session_line


@pytest.mark.parametrize(
    "payload",
    [{}, {"prompt_cache": {"warm": False, "hit_ratio": None}}],
    ids=["before-first-response", "no-input-tokens-yet"],
)
def test_statusline_without_hit_ratio_omits_cache_segment(payload: dict[str, Any]) -> None:
    session_line = _session_line(payload=payload)

    assert "cache" not in session_line


def test_statusline_configured_command_renders_the_model(bash_executable: str) -> None:
    """The command in `settings.json` must reach a working interpreter.

    It used to call `python3`, which on Windows with python.org's installer is
    the Microsoft Store stub: it prints an install hint, exits non-zero, and
    the status line stays blank. Claude Code runs the command through bash, so
    this test does too.
    """
    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    command = settings["statusLine"]["command"]

    completed = subprocess.run(
        [bash_executable, "-c", command],
        input=json.dumps({"model": {"display_name": "Opus"}}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    assert "[Opus]" in completed.stdout
