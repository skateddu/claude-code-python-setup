"""Behaviour of the `protect-main` PreToolUse hook."""

from pathlib import Path
import shutil
import subprocess
from typing import Any

import pytest

from tests.hook_harness import RunHook, bash_payload, powershell_payload

DANGEROUS_COMMANDS = [
    "git push --force origin feature",
    "git push -f origin feature",
    # Short flags cluster: -fu is --force plus --set-upstream.
    "git push -fu origin feature",
    # A leading + on a refspec force-pushes that ref.
    "git push origin +feature",
    "git push origin main",
    "git push upstream master",
    "git push -u origin main",
    # The destination is what a refspec writes to, wherever it comes from.
    "git push origin HEAD:main",
    "git push origin feature:main",
    "git push origin HEAD:refs/heads/main",
    # Deleting the remote main is a push to it too.
    "git push origin :main",
    "git push origin --delete master",
    # --all and --mirror push the local main along with everything else.
    "git push --all origin",
    "git push --mirror origin",
    # Git's global options sit between `git` and the subcommand.
    "git -C . push origin main",
    "git -c push.default=current push origin main",
    "cd src && git push --force origin feature",
    "bash -c 'git push --force origin feature'",
    "git reset --hard HEAD~1",
    "git reset HEAD~1 --hard",
    "rm -rf /",
    "rm -rf ~",
    "rm -rf ~/",
    "rm -rf .",
    "rm -rf ..",
    "rm -fr .",
    "rm -r -f /",
    "rm -R /",
    "rm --recursive --force ~",
    "rm -rf -- /",
    "rm -rf /*",
    "rm -rf ~/*",
    "rm -rf *",
    'rm -rf "$HOME"',
    "rm -rf build /",
    "sudo rm -rf /",
    "/bin/rm -rf /",
    'bash -c "rm -rf /"',
]

SAFE_COMMANDS = [
    # --force-with-lease is the sanctioned way to overwrite remote history.
    "git push --force-with-lease origin feature",
    "git push origin feature/some-work",
    # Names that merely contain a protected one.
    "git push origin main-fix",
    "git push origin feature/main",
    # Local main pushed into a remote feature branch writes to that branch only.
    "git push origin main:feature",
    "git reset --soft HEAD~1",
    # `rm` after `git` is git's subcommand, which only touches tracked files.
    "git rm -r --cached .",
    "git -C sub rm -r --cached .",
    # Specific targets that merely start with a guarded token.
    "rm -rf node_modules/",
    "rm -rf .git",
    "rm -rf ~/tmp-build-dir",
    "rm -rf ./build",
    "rm -rf build/*",
    'rm -rf "$HOME/project/build"',
    # Without -r, rm cannot remove a directory at all.
    "rm -f .",
    "ls -la",
    "git status",
]

DANGEROUS_POWERSHELL_COMMANDS = [
    "Remove-Item -Recurse -Force ~",
    "Remove-Item -Recurse -Force C:\\",
    "Remove-Item C:\\ -Recurse",
    "Remove-Item -Path . -Recurse",
    "Remove-Item -LiteralPath:.. -Recurse",
    # Parameters abbreviate to any unique prefix, and matching is case-insensitive.
    "ri -rec -force .\\*",
    "remove-item -RECURSE $HOME",
    # rm is PowerShell's alias for Remove-Item, with PowerShell's parameters.
    "rm -r -fo $env:USERPROFILE",
    "Remove-Item -Recurse -Force .\\build, ~",
    "Microsoft.PowerShell.Management\\Remove-Item -Recurse ~",
    "Set-Location C:\\work; Remove-Item -Recurse -Force .",
    "git push origin HEAD:main",
    "git push --force origin feature",
]

SAFE_POWERSHELL_COMMANDS = [
    "Remove-Item -Recurse -Force .\\build",
    "Remove-Item ~\\notes.txt",
    # -WhatIf only reports what would be deleted.
    "Remove-Item -Recurse -Force ~ -WhatIf",
    # The value of -Include is a filter, not a path to delete.
    "Remove-Item -Recurse -Include * -Path .\\src",
    "Remove-Item -Recurse:$false ~",
    "Get-ChildItem -Recurse ~",
]


@pytest.mark.parametrize("command", DANGEROUS_COMMANDS)
def test_protect_main_denies_dangerous_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", bash_payload(command))

    assert result.permission_decision == "deny", (
        f"{command!r} should be blocked, hook emitted: {result.stdout!r}"
    )


@pytest.mark.parametrize("command", SAFE_COMMANDS)
def test_protect_main_allows_safe_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", bash_payload(command))

    assert result.is_silent, f"{command!r} should pass through, hook emitted: {result.stdout!r}"
    assert result.exit_code == 0


@pytest.mark.parametrize("command", DANGEROUS_POWERSHELL_COMMANDS)
def test_protect_main_denies_dangerous_powershell_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", powershell_payload(command))

    assert result.permission_decision == "deny", (
        f"{command!r} should be blocked, hook emitted: {result.stdout!r}"
    )


@pytest.mark.parametrize("command", SAFE_POWERSHELL_COMMANDS)
def test_protect_main_allows_safe_powershell_command(run_hook: RunHook, command: str) -> None:
    result = run_hook("protect-main", powershell_payload(command))

    assert result.is_silent, f"{command!r} should pass through, hook emitted: {result.stdout!r}"
    assert result.exit_code == 0


def test_protect_main_deny_reason_names_the_alternative(run_hook: RunHook) -> None:
    result = run_hook("protect-main", bash_payload("git push --force origin feature"))

    assert "--force-with-lease" in result.reason


def test_protect_main_ignores_payload_without_command(run_hook: RunHook) -> None:
    result = run_hook("protect-main", {"tool_name": "Bash", "tool_input": {}})

    assert result.is_silent
    assert result.exit_code == 0


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """An empty git repository whose HEAD points at `main`."""
    git_executable = shutil.which("git")
    if git_executable is None:
        pytest.skip("git is required to resolve the current branch")
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run([git_executable, "init", "--quiet", str(repository)], check=True)
    _check_out(repository, branch="main")
    return repository


def _check_out(repository: Path, branch: str) -> None:
    """Point HEAD at `branch`; no commit is needed to read the current branch."""
    subprocess.run(
        ["git", "-C", str(repository), "symbolic-ref", "HEAD", f"refs/heads/{branch}"],
        check=True,
    )


def _payload_in(command: str, cwd: Path) -> dict[str, Any]:
    return {**bash_payload(command), "cwd": str(cwd)}


@pytest.mark.parametrize("command", ["git push", "git push origin", "git push origin HEAD"])
def test_protect_main_denies_implicit_push_from_main(
    run_hook: RunHook, repo_dir: Path, command: str
) -> None:
    """Without a refspec git pushes the current branch, here main."""
    result = run_hook("protect-main", _payload_in(command, cwd=repo_dir), cwd=repo_dir)

    assert result.permission_decision == "deny"


def test_protect_main_allows_implicit_push_from_feature_branch(
    run_hook: RunHook, repo_dir: Path
) -> None:
    _check_out(repo_dir, branch="feature/work")

    result = run_hook("protect-main", _payload_in("git push", cwd=repo_dir), cwd=repo_dir)

    assert result.is_silent


def test_protect_main_allows_named_feature_push_from_main(
    run_hook: RunHook, repo_dir: Path
) -> None:
    command = "git push -u origin feature/work"

    result = run_hook("protect-main", _payload_in(command, cwd=repo_dir), cwd=repo_dir)

    assert result.is_silent


def test_protect_main_resolves_implicit_push_in_git_c_directory(
    run_hook: RunHook, repo_dir: Path
) -> None:
    """`git -C <dir>` moves the repository whose current branch is pushed."""
    parent_dir = repo_dir.parent

    result = run_hook(
        "protect-main", _payload_in("git -C repo push", cwd=parent_dir), cwd=parent_dir
    )

    assert result.permission_decision == "deny"
