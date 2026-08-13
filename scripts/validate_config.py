"""Validate the Claude Code configuration this template ships."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"
MCP_CONFIG_DIR = REPO_ROOT / "mcp_config"
CLAUDE_MD_PATH = REPO_ROOT / "CLAUDE.md"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Hook entries name their script inline, e.g. "bash .claude/hooks/verify.sh".
HOOK_SCRIPT_PATTERN = re.compile(r"\.claude/hooks/[\w.-]+\.sh")
# CLAUDE.md pulls in modular rules with "@.claude/rules/<name>.md".
IMPORT_PATTERN = re.compile(r"@(\.claude/rules/[\w.-]+\.md)")
# Skills declare their identity in YAML frontmatter at the top of SKILL.md.
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)


def check_json_parses() -> list[str]:
    """Report config files that are not valid JSON.

    Returns
    -------
    list[str]
        One message per unparseable file; empty when all parse.
    """
    errors: list[str] = []
    for path in [SETTINGS_PATH, *sorted(MCP_CONFIG_DIR.glob("*.json"))]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except ValueError as error:
            errors.append(f"{path.relative_to(REPO_ROOT)}: invalid JSON -> {error}")
    return errors


def check_hook_scripts_exist() -> list[str]:
    """Report hook scripts referenced by settings.json that are missing.

    A hook pointing at a deleted script fails silently at runtime, so the
    guardrail is simply gone with no error surfaced to the user.

    Returns
    -------
    list[str]
        One message per dangling reference; empty when all resolve.
    """
    settings_text = SETTINGS_PATH.read_text(encoding="utf-8")
    referenced = sorted(set(HOOK_SCRIPT_PATTERN.findall(settings_text)))
    if not referenced:
        return ["`.claude/settings.json`: no hook scripts referenced — did the format change?"]
    return [
        f".claude/settings.json references missing hook: {reference}"
        for reference in referenced
        if not (REPO_ROOT / reference).is_file()
    ]


def check_claude_md_imports() -> list[str]:
    """Report `@`-imports in CLAUDE.md that do not resolve to a file.

    A broken import drops that rule from Claude's context without warning.

    Returns
    -------
    list[str]
        One message per unresolved import; empty when all resolve.
    """
    imports = sorted(set(IMPORT_PATTERN.findall(CLAUDE_MD_PATH.read_text(encoding="utf-8"))))
    if not imports:
        return ["CLAUDE.md: no @-imports found — did the rules section move?"]
    return [
        f"CLAUDE.md imports missing file: @{target}"
        for target in imports
        if not (REPO_ROOT / target).is_file()
    ]


def check_skill_frontmatter() -> list[str]:
    """Report skills whose SKILL.md lacks usable frontmatter.

    Claude discovers a skill through the `name` and `description` fields, so a
    skill missing either is invisible to automatic invocation.

    Returns
    -------
    list[str]
        One message per malformed skill; empty when all are well formed.
    """
    errors: list[str] = []
    for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_dir.name}: no SKILL.md")
            continue

        match = FRONTMATTER_PATTERN.match(skill_file.read_text(encoding="utf-8"))
        if match is None:
            errors.append(f"{skill_dir.name}/SKILL.md: no YAML frontmatter block")
            continue

        frontmatter = match.group(1)
        missing = [
            field
            for field in ("name", "description")
            if not re.search(rf"^{field}:", frontmatter, re.M)
        ]
        if missing:
            errors.append(f"{skill_dir.name}/SKILL.md: frontmatter missing {', '.join(missing)}")
    return errors


def main() -> int:
    """Run every check and report the outcome.

    Returns
    -------
    int
        Process exit code: 0 when every check passes, 1 otherwise.
    """
    checks = {
        "JSON config parses": check_json_parses,
        "hook scripts exist": check_hook_scripts_exist,
        "CLAUDE.md imports resolve": check_claude_md_imports,
        "skill frontmatter is complete": check_skill_frontmatter,
    }

    failures = 0
    for label, check in checks.items():
        errors = check()
        if errors:
            failures += len(errors)
            print(f"FAIL  {label}")
            for error in errors:
                print(f"      {error}")
        else:
            print(f"ok    {label}")

    if failures:
        print(f"\n{failures} problem(s) found.")
        return 1

    print("\nAll configuration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
