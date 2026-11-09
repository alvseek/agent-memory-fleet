"""The authored procedures: the served set, and the guidance each one must carry.

These assertions live in the repo that owns the content. They are about meaning rather than exact
prose — "this procedure must say a spawn is anonymous", "no active procedure may send a reader to
GitHub for the client" — so the wording can be rewritten freely while the instruction survives.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROCEDURES = ROOT / "procedures"
INSTALL_RESOURCE = "resource://client/install"
INSTALL_TOOL = 'read_resource("client-install")'
OBSOLETE_SOURCE_INSTALL = "git+https://github.com/alvseek/einherjar-server"

EXPECTED = {"ask-agent", "delegate-agent", "spawn", "load-fleet", "setup-fleet"}
CLIENT_PROCEDURES = ["ask-agent", "delegate-agent", "spawn"]
ACTIVE_PROCEDURES = ["ask-agent", "delegate-agent", "spawn", "load-fleet"]


def _text(name: str) -> str:
    return (PROCEDURES / f"{name}.md").read_text(encoding="utf-8")


def test_the_served_set_is_exactly_these_procedures() -> None:
    assert {path.stem for path in PROCEDURES.glob("*.md")} == EXPECTED


@pytest.mark.parametrize("name", CLIENT_PROCEDURES)
def test_client_procedures_point_at_the_served_wheel(name: str) -> None:
    """A reader is sent to the running server's install resource, never to a package index."""
    text = _text(name)
    assert INSTALL_RESOURCE in text
    assert INSTALL_TOOL in text
    assert "uv tool install --force" in text


@pytest.mark.parametrize("name", ACTIVE_PROCEDURES)
def test_no_active_procedure_installs_the_client_from_github(name: str) -> None:
    text = _text(name)
    assert OBSOLETE_SOURCE_INSTALL not in text
    assert "uv tool install einherjar" not in text


def test_the_readme_does_not_install_the_client_from_github() -> None:
    assert OBSOLETE_SOURCE_INSTALL not in (ROOT / "README.md").read_text(encoding="utf-8")


# --- /spawn -------------------------------------------------------------------------------


def test_spawn_is_anonymous_and_asks_for_no_awakening() -> None:
    text = _text("spawn")
    assert "no fleet agent name" in text
    assert "no awakening" in text
    assert "no fleet identity" in text
    # The procedure must never instruct its reader to awaken a session.
    assert "awaken as" not in text.lower()


def test_spawn_carries_the_structured_prompt() -> None:
    text = _text("spawn")
    for heading in ("## Theme", "## Context", "## Request", "## Expected Output"):
        assert heading in text


def test_spawn_covers_foreground_background_results_and_resume() -> None:
    text = _text("spawn")
    assert "einherjar spawn --prompt" in text
    assert "--background" in text
    assert "einherjar result <SessionRef>" in text
    assert "einherjar ask <SessionRef>" in text
    assert "--theme" in text
    assert "--model" in text


def test_spawn_states_the_lifecycle_and_the_honest_completion_rule() -> None:
    text = _text("spawn")
    assert "not a memory wrap-up" in text
    assert "closed `completed`" in text
    assert "not that anything was remembered" in text


def test_spawn_forbids_overlapping_turns_and_names_the_platform_selection() -> None:
    text = _text("spawn")
    assert "Do not run overlapping turns" in text
    assert "EINHERJAR_PLATFORM=claude|opencode" in text
    assert "ses_" in text
    assert "UUID" in text


def test_spawn_sends_a_long_task_to_a_task_file() -> None:
    """The documented safe form for a multiline task, without inventing a new CLI flag."""
    text = _text("spawn")
    assert "task file" in text
    assert "truncated" in text
    assert "--prompt-file" not in text


def test_spawn_reads_result_as_a_file_not_a_running_flag() -> None:
    """`result` prints a file created at spawn time; it cannot prove a turn is running."""
    text = _text("spawn")
    assert "creates that ref's output file when it spawns the turn" in text
    assert "an empty file is normal" in text
    assert "not evidence that a background turn is still running" in text
    # A foreground turn never writes one, which is why the ref is the only record of it.
    assert "a foreground turn writes no" in text
    assert "never as proof" in text


def test_delegate_reads_result_as_a_file_and_needs_no_sign_in() -> None:
    text = _text("delegate-agent")
    assert "creates that file when it spawns the turn" in text
    assert "empty while the turn is still running" in text
    assert "not proof that a background turn is merely unfinished" in text
    assert "needs no sign-in" in text


@pytest.mark.parametrize(
    ("name", "prescribed"),
    [
        ("ask-agent", "and repeat the consult"),
        ("delegate-agent", "and repeat the command"),
    ],
)
def test_no_procedure_prescribes_repeating_a_dispatched_turn(
    name: str, prescribed: str
) -> None:
    """Registry auth covers tracking; the turn already ran, so repeating it duplicates work."""
    text = _text(name)
    assert prescribed not in text
    assert "tracking" in text


def test_spawn_forbids_repeating_a_spawn_for_a_lapsed_sign_in() -> None:
    text = _text("spawn")
    assert "Do not repeat the spawn" in text
    assert "duplicates the work" in text
    assert "still ran" in text


def test_spawn_does_not_claim_the_prompt_escapes_shell_quoting() -> None:
    """A short single-line argument is still quoted; only long multiline values truncate."""
    text = _text("spawn")
    assert "does not depend on shell quoting" not in text
    assert "single-line" in text
    assert "truncat" in text


@pytest.mark.parametrize("name", CLIENT_PROCEDURES)
def test_the_login_guidance_describes_refresh_not_a_hourly_sign_in(name: str) -> None:
    """Consent buys a refresh token, so the client renews rather than asking every hour.

    Regression: these procedures used to tell a reader this client was issued no refresh token and
    had to sign in again whenever the access token expired.
    """
    text = _text(name)
    assert "no refresh token" not in text
    assert "refresh" in text
    assert "consent" in text


def test_the_fleet_readme_describes_consent_and_refresh() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "no refresh token" not in text
    assert "consent" in text
    assert "renews" in text
