#!/usr/bin/env python3
"""Remove the agent-memory-fleet (hermod-fleet) OpenCode install.

The inverse of ``setup-all-opencode.py``, scoped to this layer only: it removes the skill folders
this layer's manifest claims, deletes that manifest, and removes this layer's own lines (its path
definition, and its access declaration if it has one) from the OpenCode global instructions file.
It never touches a folder another layer's manifest claims, the other layers' lines, or the data
store.

Idempotent: a second run finds nothing left to remove.

Usage:        python setup-scripts/uninstall-opencode.py [--yes]
Env override: AGENT_MEMORY_TARGET_DIR   (default: ~/.config/opencode/skills)
              AGENT_MEMORY_AGENTS_FILE  (default: ~/.config/opencode/AGENTS.md)
"""

from __future__ import annotations

import datetime
import os
import shutil
import sys
from pathlib import Path

_MANIFEST_NAME = ".agent-memory-fleet-opencode-manifest"
_SKILL_PREFIX = "agent-fleet-"
_SIBLING_MANIFEST_NAMES = [
    ".agent-memory-opencode-manifest",
    ".agent-memory-project-opencode-manifest",
    ".agent-memory-local-opencode-manifest",
    ".agent-memory-wizards-opencode-manifest",
]
# Comment tags this layer's own definitions carry in the global file.
_OWN_MARKERS = [
    "34ca859f-6586-4990-b729-23f834c8aaae",
    "40ab1e33-4da7-4687-bd20-796c1a9caf7a",
]

DEFAULT_SKILLS_DIR = Path.home() / ".config" / "opencode" / "skills"
DEFAULT_AGENTS_FILE = Path.home() / ".config" / "opencode" / "AGENTS.md"


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def remove_skills(target_dir: Path) -> list[str]:
    """Remove this layer's skill folders -- those its manifest claims, plus any orphan carrying
    its prefix -- never one a sibling manifest claims."""
    if not target_dir.is_dir():
        return []
    sibling: set[str] = set()
    for name in _SIBLING_MANIFEST_NAMES:
        sibling |= set(_read_lines(target_dir / name))

    claimed = set(_read_lines(target_dir / _MANIFEST_NAME))
    # Also catch prefixed orphans a lost or partial manifest would miss.
    for entry in target_dir.iterdir():
        if entry.is_dir() and entry.name.startswith(_SKILL_PREFIX):
            claimed.add(entry.name)

    removed: list[str] = []
    for name in sorted(claimed):
        if name in sibling:
            continue
        folder = target_dir / name
        if folder.is_dir():
            shutil.rmtree(folder)
            removed.append(name)

    manifest = target_dir / _MANIFEST_NAME
    if manifest.is_file():
        manifest.unlink()
    return removed


def strip_own_lines(agents_file: Path) -> str:
    """Remove this layer's own definition lines (path def + access declaration), leaving every
    other layer's lines and the core memory untouched. Backs up first."""
    if not agents_file.is_file():
        return f"no {agents_file.name} found -- nothing to strip"
    text = agents_file.read_text(encoding="utf-8")
    if not any(m in text for m in _OWN_MARKERS):
        return f"{agents_file.name} has none of this layer's lines -- left untouched"

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = agents_file.with_name(f"{agents_file.name}.bak-{stamp}")
    shutil.copyfile(agents_file, backup)

    kept = [ln for ln in text.splitlines() if not any(m in ln for m in _OWN_MARKERS)]
    agents_file.write_text("\n".join(kept).rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    return f"removed this layer's lines from {agents_file.name}; backup at {backup.name}"


def main(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    auto_yes = "--yes" in args

    skills_dir = Path(os.environ.get("AGENT_MEMORY_TARGET_DIR") or DEFAULT_SKILLS_DIR)
    agents_file = Path(os.environ.get("AGENT_MEMORY_AGENTS_FILE") or DEFAULT_AGENTS_FILE)

    print("=== Uninstall agent-memory-fleet (hermod-fleet) (OpenCode) ===\n")
    print(f"Skills dir:   {skills_dir}")
    print(f"Instructions: {agents_file}\n")

    if not auto_yes:
        try:
            answer = input("Remove this layer's OpenCode install? (y/N) ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1
        if answer.lower() not in ("y", "yes"):
            print("Cancelled.")
            return 1
        print()

    removed = remove_skills(skills_dir)
    if removed:
        print(f"Removed {len(removed)} skill(s):")
        for name in removed:
            print(f"  - {name}")
    else:
        print("No skills to remove.")

    print()
    print(f"Instructions: {strip_own_lines(agents_file)}")
    print()
    print("Left in place: every other layer's skills/manifest/definitions, and the data store.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
