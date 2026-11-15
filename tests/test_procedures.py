"""Authored workflow contracts; prose checks are not runtime verification."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROCEDURES = ROOT / "procedures"
EXPECTED = {"ask-agent", "delegate-agent", "spawn", "dispatch-plan", "load-fleet", "setup-fleet"}
CLIENT_PROCEDURES = ["ask-agent", "delegate-agent", "spawn", "dispatch-plan"]


def text(name: str) -> str:
    return (PROCEDURES / f"{name}.md").read_text(encoding="utf-8")


def test_served_set() -> None:
    assert {p.stem for p in PROCEDURES.glob("*.md")} == EXPECTED


@pytest.mark.parametrize("name", CLIENT_PROCEDURES)
def test_install_and_registry_contract(name: str) -> None:
    body = text(name)
    for phrase in (
        "resource://client/install",
        'read_resource("client-install")',
        "uv tool install --force",
        "consent",
        "refresh",
        "tracking",
    ):
        assert phrase in body
    assert "git+https://" not in body
    assert "uv tool install einherjar" not in body


@pytest.mark.parametrize("name", ["delegate-agent", "dispatch-plan", "spawn"])
def test_notification_is_platform_owned(name: str) -> None:
    body = text(name)
    for phrase in ("blocking", "OpenCode", "Claude Code", "completion", "timeout", "poll"):
        assert phrase in body
    assert "sleep" in body
    assert "overlapping turns" in body
    assert "closed" in body or "closing" in body or "closure" in body


@pytest.mark.parametrize("name", ["ask-agent", "delegate-agent"])
def test_no_target_is_anonymous_not_an_identity_question(name: str) -> None:
    body = text(name)
    assert "spawn" in body
    assert "no awakening" in body or "without an identity or awakening" in body
    assert "Which agent do you want" not in body
    assert "SessionRef" in body


def test_spawn_is_anonymous_and_resumable() -> None:
    body = text("spawn")
    for phrase in (
        "no fleet agent name",
        "no awakening",
        "no fleet identity",
        "einherjar ask <SessionRef>",
        "not a memory wrap-up",
        "not that anything was remembered",
    ):
        assert phrase in body
    assert "awaken as" not in body.lower()
    for heading in ("## Theme", "## Context", "## Request", "## Expected Output"):
        assert heading in body


@pytest.mark.parametrize("name", CLIENT_PROCEDURES)
def test_prompt_file_and_explicit_model_contract(name: str) -> None:
    body = text(name)
    assert "single-line" in body
    assert "truncat" in body
    assert "model" in body
    assert "unmapped" in body or "unresolved" in body


def test_dispatch_inputs_and_precedence() -> None:
    body = text("dispatch-plan")
    for phrase in (
        "--plan",
        "--rules",
        "--agent",
        "--model",
        "either order",
        "filenames alone",
        "plain Markdown",
        "optional YAML",
        "YAML is not required",
        "override",
        "missing model",
    ):
        assert phrase in body
    assert "no mode setting" in body.lower()


def test_dispatch_full_read_handoff_and_announcement() -> None:
    body = text("dispatch-plan")
    for phrase in (
        "Read both documents fully",
        "truncated",
        "implement-plan",
        "[PROJECT-ACCESS]",
        "read_procedure",
        "task file",
        "announcement, not a confirmation",
        "proceed without waiting",
        "exclusive ownership",
        "Acceptance Criteria",
        "Expected Output",
    ):
        assert phrase in body


def test_dispatch_supervision_and_human_gates() -> None:
    body = text("dispatch-plan")
    for phrase in (
        "same worker",
        "same-resolved-model",
        "not that the plan is finished",
        "verification evidence",
        "STOP/sign-off",
        "scope changes",
        "costly to reverse",
        "Do not archive",
        "Anonymous workers",
        "duplicate",
        "registry 401",
    ):
        assert phrase in body


@pytest.mark.parametrize("name", CLIENT_PROCEDURES)
def test_procedures_never_prescribe_removed_cli_launches(name: str) -> None:
    # Mentioning a removed form in migration prose is fine; emitting a command is not.
    lines = text(name).splitlines()
    commands = [line.strip() for line in lines if line.strip().startswith("einherjar ")]
    assert not any(line.startswith("einherjar delegate ") for line in commands)
    assert not any(
        line.startswith("einherjar spawn ") and "--background" in line for line in commands
    )


def test_historical_results_are_not_live_completion() -> None:
    for name in CLIENT_PROCEDURES:
        body = text(name)
        assert "historical" in body
        assert "current command result" in body or "current turn" in body


def test_readme_and_load_fleet_offer_dispatch() -> None:
    for body in (text("load-fleet"), (ROOT / "README.md").read_text(encoding="utf-8")):
        assert "dispatch-plan" in body
        assert "einherjar delegate ..." not in body
        assert "spawn --prompt ... [--background]" not in body


@pytest.mark.parametrize("name", ["ask-agent", "spawn", "dispatch-plan"])
def test_alias_documentation_handles_powershell_dotted_keys(name: str) -> None:
    body = text(name)
    assert "hyphens" in body
    assert "dots" in body
    assert "${env:EINHERJAR_MODEL_DEEPSEEK_V4.1_FLASH}" in body
