"""Install the agent-memory-fleet procedures as Antigravity **Agent Skills**.

Replaces the old ``setup-all-antigravity.sh``, which wrote flat markdown into
``~/.gemini/workflows`` — wrong on three counts: that is not where Antigravity looks, workflows
are being retired in favour of skills, and a workflow file is capped at 12,000 characters while
sixteen of this overlay's compiled procedures exceed it (``pixel-wizard`` is 35k). Skills have
no such cap; the emitter's module docstring records the measurement.

Antigravity reads global skills from ``~/.gemini/config/skills``, which is the path that serves
every Antigravity product rather than one surface of it. Workspace-scoped skills live in a
repo's own ``.agents/skills`` and are not this installer's business.

This overlay composes ON TOP OF the memory core (agent-memory-system); install the core too by
running its own installer. Each installer owns its manifest and cleans up independently, so the
two coexist in one skills directory and neither deletes a skill the other claims.

Usage:        python setup-scripts/setup-all-antigravity.py
Env override: AGENT_MEMORY_TARGET_DIR (default: ~/.gemini/config/skills)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "overlay_install_skills", _ROOT / "setup-scripts" / "install-skills.py"
)
_skills = importlib.util.module_from_spec(_spec)
sys.modules["overlay_install_skills"] = _skills
_spec.loader.exec_module(_skills)

MANIFEST_NAME = ".agent-memory-fleet-antigravity-manifest"
CORE_MANIFEST_NAME = ".agent-memory-antigravity-manifest"
PROJECT_MANIFEST_NAME = ".agent-memory-project-antigravity-manifest"
LOCAL_MANIFEST_NAME = ".agent-memory-local-antigravity-manifest"


def main(argv: list[str] | None = None) -> int:
    target = Path(
        os.environ.get("AGENT_MEMORY_TARGET_DIR")
        or Path.home() / ".gemini" / "config" / "skills"
    )
    return _skills.run(
        platform="Antigravity",
        target_dir=target,
        manifest_name=MANIFEST_NAME,
        sibling_manifest_names=[CORE_MANIFEST_NAME, PROJECT_MANIFEST_NAME, LOCAL_MANIFEST_NAME],
        instructions_file=Path.home() / ".gemini" / "GEMINI.md",
    )


if __name__ == "__main__":
    raise SystemExit(main())
