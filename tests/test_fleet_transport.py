"""The fleet's platform branch, pinned without spawning an agent.

``FLEET_DRY_RUN=1`` makes ``run_agent_turn`` print the argv it would execute, so the two arms
can be asserted on any machine. The scripts are bash, so the suite skips where no usable bash
exists: on Windows the first ``bash`` on PATH is the WSL launcher, which cannot read a Windows
path, so Git Bash is tried explicitly before whatever PATH offers.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "fleet-scripts"


def _usable_bash() -> str | None:
    candidates: list[str] = []
    if sys.platform == "win32":
        for base in (
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("LocalAppData", "") + r"\Programs",
        ):
            if base:
                candidates.append(str(Path(base) / "Git" / "bin" / "bash.exe"))
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    for candidate in candidates:
        if not Path(candidate).is_file():
            continue
        try:
            probe = subprocess.run(
                [candidate, "-c", "echo ok"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if probe.returncode == 0 and probe.stdout.strip() == "ok":
            return candidate
    return None


BASH = _usable_bash()
pytestmark = pytest.mark.skipif(BASH is None, reason="no usable bash on this machine")


def _posix(path: Path) -> str:
    return str(path).replace("\\", "/")


def _run_ask(tmp_path: Path, target: str, platform: str | None, model: str = "") -> str:
    """Run ask-agent.sh in dry-run mode and return its last stdout line (the argv)."""
    memory = tmp_path / "memory"
    (memory / "agent-backend-django").mkdir(parents=True)
    (tmp_path / "fleet-agents.md").write_text(
        "| Agent Domain | Specialty | When to Consult | Model |\n"
        "|---|---|---|---|\n"
        "| Backend Django | APIs | backend work | sonnet |\n",
        encoding="utf-8",
    )
    fleet_map = tmp_path / "fleet-map.csv"

    env = dict(os.environ)
    env["FLEET_DRY_RUN"] = "1"
    env["AGENT_MEMORY_PATH"] = _posix(memory)
    env["FLEET_MODEL_SONNET"] = "commandcode/claude-sonnet-5-5"
    for marker in ("FLEET_PLATFORM", "OPENCODE", "AI_AGENT", "PROJECT_ACCESS", "CODING_ACCESS"):
        env.pop(marker, None)
    if platform:
        env["FLEET_PLATFORM"] = platform

    result = subprocess.run(
        [
            BASH,
            _posix(SCRIPTS / "ask-agent.sh"),
            target,
            "hello",
            "theme",
            _posix(fleet_map),
            model,
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=_posix(tmp_path),
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


def test_claude_new_session_uses_session_id(tmp_path: Path) -> None:
    argv = _run_ask(tmp_path, "Backend Django", "claude")
    assert argv.startswith("claude --print")
    assert "--session-id" in argv
    assert "--model sonnet" in argv
    # The fleet never forces a permission bypass on the user's behalf.
    assert "--dangerously-skip-permissions" not in argv


def test_opencode_new_session_uses_session_and_auto(tmp_path: Path) -> None:
    argv = _run_ask(tmp_path, "Backend Django", "opencode")
    assert argv.startswith("opencode run --session ses_")
    assert "--auto" in argv
    assert "--model commandcode/claude-sonnet-5-5" in argv


def test_uuid_ref_resumes_on_claude(tmp_path: Path) -> None:
    argv = _run_ask(tmp_path, "3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f", "opencode")
    assert argv.startswith("claude --print --resume")
    assert "--session-id" not in argv


def test_ses_ref_resumes_on_opencode(tmp_path: Path) -> None:
    argv = _run_ask(tmp_path, "ses_abc123def456", "claude")
    assert argv.startswith("opencode run --session ses_abc123def456")
    assert "--auto" in argv


def test_platform_is_detected_from_the_caller_environment(tmp_path: Path) -> None:
    env = dict(os.environ)
    env.update({"OPENCODE": "1", "AI_AGENT": "opencode"})
    env.pop("FLEET_PLATFORM", None)
    env["FLEET_DRY_RUN"] = "1"
    memory = tmp_path / "memory"
    (memory / "agent-backend-django").mkdir(parents=True)
    env["AGENT_MEMORY_PATH"] = _posix(memory)
    result = subprocess.run(
        [
            BASH,
            _posix(SCRIPTS / "ask-agent.sh"),
            "Backend Django",
            "hello",
            "theme",
            _posix(tmp_path / "fleet-map.csv"),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=_posix(tmp_path),
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1].startswith("opencode run --session ses_")


def test_an_old_map_is_upgraded_before_it_is_written(tmp_path: Path) -> None:
    fleet_map = tmp_path / "fleet-map.csv"
    fleet_map.write_text(
        "agent_domain,uuid,awakened,task_theme,status\n"
        "Backend Django,3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f,2026-10-01 10:00,old work,active\n",
        encoding="utf-8",
    )
    _run_ask(tmp_path, "Backend Django", "claude")

    lines = fleet_map.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "agent_domain,session_ref,platform,awakened,task_theme,status"
    assert lines[1].split(",")[2] == "claude"
    assert lines[1].split(",")[1] == "3f8a2b1c-9d4e-4f7a-8e2b-5c6d9a1b4e7f"
    # The new entry carries the platform it was spawned on.
    assert lines[-1].split(",")[2] == "claude"
