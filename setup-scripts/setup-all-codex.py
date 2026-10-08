"""Install the agent-memory-fleet OVERLAY procedures as Codex **Agent Skills**.

Replaces the old ``setup-all-codex.sh``. That script had the right target and the right shape —
Codex's documented user scope really is ``$HOME/.agents/skills``, not the ``~/.codex/skills``
most write-ups name, which is where Codex keeps its own bundled skills. What it got wrong was
*what* it installed: it copied ``procedures/*.md``, the raw source, so components were never
inlined and every installed skill referenced fragments that do not exist at the target. This
installs the **compiled** output, which is self-contained.

Codex deprecated custom prompts (``~/.codex/prompts``) in favour of skills, so skills are also
the only forward-looking channel.

This overlay composes ON TOP OF the memory core (agent-memory-system); install the core too by
running its own installer. Each installer owns its manifest and cleans up independently, so the
two coexist in one skills directory and neither deletes a skill the other claims.

Usage:        python setup-scripts/setup-all-codex.py
Env override: AGENT_MEMORY_TARGET_DIR (default: ~/.agents/skills)
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

MANIFEST_NAME = ".agent-memory-fleet-codex-manifest"
CORE_MANIFEST_NAME = ".agent-memory-codex-manifest"
CODING_MANIFEST_NAME = ".agent-memory-coding-skill-codex-manifest"


def main(argv: list[str] | None = None) -> int:
    target = Path(
        os.environ.get("AGENT_MEMORY_TARGET_DIR") or Path.home() / ".agents" / "skills"
    )
    return _skills.run(
        platform="Codex",
        target_dir=target,
        manifest_name=MANIFEST_NAME,
        sibling_manifest_names=[CORE_MANIFEST_NAME, CODING_MANIFEST_NAME],
        instructions_file=Path.home() / ".codex" / "AGENTS.md",
    )


if __name__ == "__main__":
    raise SystemExit(main())
