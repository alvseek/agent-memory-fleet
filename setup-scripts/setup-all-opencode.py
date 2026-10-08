"""Install the agent-memory-fleet OVERLAY procedures as OpenCode **Agent Skills**.

OpenCode discovers global skills as folders holding a ``SKILL.md`` with ``name`` and
``description`` frontmatter in ``~/.config/opencode/skills/`` (``$XDG_CONFIG_HOME/opencode/skills/``
when ``XDG_CONFIG_HOME`` is set). Skills are **model-invoked**: the agent sees each skill's name
and description at every step and loads the body itself when a task matches — which is why
skills fit this overlay better than slash commands here. Commands have to be typed (``/name``);
no user is going to type ``/map-qa-instrument`` from memory, so the procedures would sit idle.
With skills, the agent reaches for them on its own.

Installed folders carry the overlay's ``agent-fleet-`` prefix — deliberately distinct from
the core's ``agent-memory-`` one — so the skill catalog stays legible and each installer's
manifest claims an unambiguous set: that prefix separation is what keeps the 38 overlay skills
from crowding anything else out, and keeps a same-named core procedure from ever sharing (and
clobbering) an overlay folder.

This overlay composes ON TOP OF the memory core (agent-memory-system); install the core too by
running its own installer. Each installer owns its manifest and cleans up independently, so the
two coexist in one skills directory and neither deletes a skill the other claims.

Replaces the earlier commands-based revision of this installer (``~/.config/opencode/commands/``):
installing now also removes those legacy command files, so the two generations never pile up.

Cross-platform: run directly on macOS/Linux, or via the ``.bat`` wrapper on Windows.

Usage:        python setup-scripts/setup-all-opencode.py
Env override: AGENT_MEMORY_TARGET_DIR (default: ~/.config/opencode/skills)
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

MANIFEST_NAME = ".agent-memory-fleet-opencode-manifest"
CORE_MANIFEST_NAME = ".agent-memory-opencode-manifest"


def _config_base() -> Path:
    """Base dir for OpenCode global state (respects XDG on Linux/macOS)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "opencode"
    return Path.home() / ".config" / "opencode"


def _migrate_from_commands(commands_dir: Path) -> int:
    """Remove overlay commands left by the previous commands-based installer.

    The first generation of this installer wrote flat ``<name>.md`` files into the global
    commands directory. Skills supersede them now, so anything that manifest still claims is
    deleted — except a file the sibling (core) manifest also claims, which the core owns.
    The legacy manifest itself is removed once it has nothing left to claim.
    """
    manifest = commands_dir / MANIFEST_NAME
    if not manifest.exists():
        return 0
    sibling: set[str] = set()
    sibling_manifest = commands_dir / CORE_MANIFEST_NAME
    if sibling_manifest.exists():
        raw = sibling_manifest.read_text(encoding="utf-8").splitlines()
        sibling = {ln.strip() for ln in raw if ln.strip()}
    removed = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        fname = line.strip()
        if not fname or fname in sibling:
            continue
        target = commands_dir / fname
        if target.is_file():
            target.unlink()
            removed += 1
    manifest.unlink()
    return removed


def main(argv: list[str] | None = None) -> int:
    base = _config_base()
    target = Path(os.environ.get("AGENT_MEMORY_TARGET_DIR") or base / "skills")

    legacy_removed = 0
    commands_dir = base / "commands"
    if commands_dir != target:
        legacy_removed = _migrate_from_commands(commands_dir)

    rc = _skills.run(
        platform="OpenCode",
        target_dir=target,
        manifest_name=MANIFEST_NAME,
        sibling_manifest_name=CORE_MANIFEST_NAME,
        instructions_file=base / "AGENTS.md",
    )
    if legacy_removed:
        print(
            f"\nMigrated away from commands: removed {legacy_removed} "
            f"legacy command files from {commands_dir}"
        )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
