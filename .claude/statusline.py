"""Claude Code status line: model, git, context bar, cost, duration."""

import json
import os
import subprocess
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")

# ANSI colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

CACHE_FILE = os.path.join(tempfile.gettempdir(), "statusline-git-cache")
CACHE_MAX_AGE = 5
BAR_WIDTH = 10


def _progress_bar(percentage: int, width: int = BAR_WIDTH) -> str:
    """Return a colored progress bar string based on usage percentage.

    Parameters
    ----------
    percentage
        Usage value from 0 to 100. Higher means more consumed.
    width
        Number of characters in the bar.
    """
    if percentage >= 90:
        color = RED
    elif percentage >= 70:
        color = YELLOW
    else:
        color = GREEN

    filled = percentage * width // 100
    bar = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{RESET}"


def _git(cwd: str, *args: str) -> str:
    """Run a git command and return stripped stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "--no-optional-locks", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _git_info(cwd: str) -> tuple[str, int, int]:
    """Return (branch, staged_count, modified_count) with 5s cache."""
    is_stale = True
    if os.path.exists(CACHE_FILE):
        age = time.time() - os.path.getmtime(CACHE_FILE)
        is_stale = age > CACHE_MAX_AGE

    if is_stale:
        if cwd and _git(cwd, "rev-parse", "--git-dir"):
            branch = _git(cwd, "branch", "--show-current")
            staged_out = _git(cwd, "diff", "--cached", "--numstat")
            modified_out = _git(cwd, "diff", "--numstat")
            staged = len(staged_out.splitlines()) if staged_out else 0
            modified = len(modified_out.splitlines()) if modified_out else 0
            with open(file=CACHE_FILE, mode="w") as file:
                file.write(f"{branch}|{staged}|{modified}")
        else:
            with open(file=CACHE_FILE, mode="w") as file:
                file.write("||")

    with open(file=CACHE_FILE) as file:
        parts = file.read().strip().split(sep="|")

    branch = parts[0] if len(parts) > 0 else ""
    staged = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    modified = int(parts[2]) if len(parts) > 2 and parts[2] else 0
    return branch, staged, modified


def main() -> None:
    data = json.load(fp=sys.stdin)

    model = data.get("model", {}).get("display_name", "unknown")
    cwd = data.get("workspace", {}).get("current_dir", "")
    cost = data.get("cost", {}).get("total_cost_usd", 0) or 0
    pct = int(data.get("context_window", {}).get("used_percentage", 0) or 0)
    duration_ms = data.get("cost", {}).get("total_duration_ms", 0) or 0

    # --- Line 1: model, directory, git ---
    dir_name = os.path.basename(cwd) if cwd else ""
    branch, staged, modified = _git_info(cwd)

    git_info = ""
    if branch:
        git_status = ""
        if staged > 0:
            git_status += f" {GREEN}+{staged}{RESET}"
        if modified > 0:
            git_status += f" {YELLOW}~{modified}{RESET}"
        git_info = f" | {branch}{git_status}"

    print(f"model: {CYAN}[{model}]{RESET} | directory: {dir_name}{git_info}")

    # --- Line 2: context bar, cost, duration ---
    mins = duration_ms // 60000
    secs = (duration_ms % 60000) // 1000

    print(f"session: {_progress_bar(pct)} {pct}% | {YELLOW}${cost:.2f}{RESET} | {mins}m {secs}s")

    # --- Line 3: rate limits (Pro/Max only, absent until first API response) ---
    rate_limits = data.get("rate_limits", {})
    five_h_used = rate_limits.get("five_hour", {}).get("used_percentage")
    seven_d_used = rate_limits.get("seven_day", {}).get("used_percentage")

    parts = []
    if five_h_used is not None:
        five_h_pct = int(five_h_used)
        parts.append(f"5h {_progress_bar(percentage=five_h_pct)} {five_h_pct}%")

    if seven_d_used is not None:
        seven_d_pct = int(seven_d_used)
        parts.append(f"7d {_progress_bar(percentage=seven_d_pct)} {seven_d_pct}%")

    if parts:
        print(f"rate limits: {' | '.join(parts)}", end="")


if __name__ == "__main__":
    main()
