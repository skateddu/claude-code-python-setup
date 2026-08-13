"""Behaviour of the `guard-secrets` UserPromptSubmit hook.

The credentials here are syntactically valid but deliberately fake. They are
also assembled at runtime from fragments rather than written out literally, so
the repository never contains a contiguous string matching a real credential
format — which would otherwise trip GitHub push protection and secret scanners
on a file whose whole purpose is to carry credential-shaped text.
"""

import pytest

from tests.hook_harness import RunHook

_FILLER_36 = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
_ZEROS_24 = "0" * 24

PROMPTS_WITH_SECRETS = [
    # AWS publishes this exact key as its documentation example.
    ("aws access key", "Use AKIA" + "IOSFODNN7EXAMPLE for the deploy"),
    ("github pat", "token is gh" + "p_" + _FILLER_36),
    ("github oauth token", "here: gh" + "o_" + _FILLER_36),
    ("anthropic key", "export ANTHROPIC_API_KEY=sk-" + "ant-api03-" + _ZEROS_24),
    ("google api key", "AIza" + "Sy" + "A" + "0" * 34),
    ("slack token", "xox" + "b-0000000000-0000000000-abcdefghijklmnop"),
    ("pem private key", "-----BEGIN RSA PRIVATE KEY" + "-----\nMIIE...\n"),
]

BENIGN_PROMPTS = [
    "Refactor the auth service to use dependency injection",
    "The API key lives in .env, load it with pydantic-settings",
    "Why does AKIA appear in the AWS docs?",
    "Explain what sk-ant keys are used for",
    "What prefix do GitHub personal access tokens use?",
]


@pytest.mark.parametrize(
    ("label", "prompt"),
    PROMPTS_WITH_SECRETS,
    ids=[label for label, _ in PROMPTS_WITH_SECRETS],
)
def test_guard_secrets_blocks_prompt_with_credential(
    run_hook: RunHook, label: str, prompt: str
) -> None:
    result = run_hook("guard-secrets", {"prompt": prompt})

    assert result.decision == "block", (
        f"{label} should be blocked, hook emitted: {result.stdout!r}"
    )
    assert "secret" in result.reason.lower()


@pytest.mark.parametrize("prompt", BENIGN_PROMPTS)
def test_guard_secrets_allows_benign_prompt(run_hook: RunHook, prompt: str) -> None:
    result = run_hook("guard-secrets", {"prompt": prompt})

    assert result.is_silent, f"{prompt!r} should pass through, hook emitted: {result.stdout!r}"
    assert result.exit_code == 0


def test_guard_secrets_ignores_empty_prompt(run_hook: RunHook) -> None:
    result = run_hook("guard-secrets", {"prompt": ""})

    assert result.is_silent
    assert result.exit_code == 0
