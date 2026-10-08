"""Install the agent-memory-fleet OVERLAY procedures as ``~/.claude/commands/``.

Compiles the coding/repo overlay procedures (wizards, doc-gen, QA, fleet, map-orientation,
localize-context, wait-options, push/pull, project-wrap-up, awaken-coder) via
``compile-procedures.py``, then installs the **compiled** self-contained commands — so an
installed command carries no reference to ``components/`` or ``templates/``.

This overlay composes ON TOP OF the memory core (agent-memory-system); install the core too by
running its own installer. Each installer owns its own manifest and cleans up independently, so
the two coexist in the same target dir — and neither ever deletes a command the other claims.

Cross-platform (replaces the old ``.sh``): run directly on macOS/Linux, or via the ``.bat``
wrapper on Windows.

Usage:        python setup-scripts/setup-all-claude-code.py
Env override: AGENT_MEMORY_TARGET_DIR (default: ~/.claude/commands)
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

# Repo root (this script lives at setup-scripts/setup-all-claude-code.py).
_ROOT = Path(__file__).resolve().parents[1]

_MANIFEST_NAME = ".agent-memory-fleet-manifest"
_SIBLING_MANIFEST_NAMES = [".agent-memory-manifest", ".agent-memory-coding-skill-manifest"]

# Marks the overlay-path definition line in the global CLAUDE.md so re-runs never duplicate it.
_PATH_DEF_UUID = "34ca859f-6586-4990-b729-23f834c8aaae"

# Marks the fleet-layer access declaration ([FLEET-ACCESS] / [FLEET-MCP-URL]) this installer writes.
_FLEET_ACCESS_UUID = "40ab1e33-4da7-4687-bd20-796c1a9caf7a"


def _load(name: str, path: Path):
    """Load a hyphen-named sibling script by file path (reusing an already-loaded copy)."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_cc = _load("overlay_compile", _ROOT / "setup-scripts" / "compile-procedures.py")


def _cleanup(target_dir: Path, manifest: Path, sibling_manifests: list[Path]) -> int:
    """Remove previously installed fleet commands, per the fleet manifest.

    Never deletes a file that any sibling manifest also claims: a stale entry, e.g. a command that
    moved between repos in a prior session, must not delete a command another installer owns. This
    is what makes the installers order-independent.
    """
    if not manifest.exists():
        return 0
    sibling: set[str] = set()
    for sibling_manifest in sibling_manifests:
        if sibling_manifest.exists():
            raw = sibling_manifest.read_text(encoding="utf-8").splitlines()
            sibling |= {ln.strip() for ln in raw if ln.strip()}
    removed = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        fname = line.strip()
        if not fname or fname in sibling:
            continue
        target = target_dir / fname
        if target.is_file():
            target.unlink()
            removed += 1
    return removed


def _register_overlay_path(claude_md: Path, overlay_root: Path) -> str:
    """Define ``[path-to-agent-memory-fleet]`` in the global CLAUDE.md (idempotent).

    The overlay's procedures reference their scripts via that placeholder, and only this
    installer knows where the standalone repo was cloned — so it registers the definition
    itself, UUID-guarded so re-runs don't duplicate the line.

    The path is written with forward slashes: that form is accepted by Windows tooling *and* by
    the bash that runs the overlay's ``scripts/*.sh``, whereas a backslash path would be mangled
    as escape sequences by bash. On macOS/Linux it is just the ordinary path.
    """
    if not claude_md.is_file():
        return (
            f"  NOTE: {claude_md} not found — could not register\n"
            "        [path-to-agent-memory-fleet]. Run the memory-core setup first\n"
            "        (it creates CLAUDE.md), then re-run this installer."
        )
    if _PATH_DEF_UUID in claude_md.read_text(encoding="utf-8"):
        return "  [path-to-agent-memory-fleet] already registered in CLAUDE.md — skipped."

    path_value = overlay_root.as_posix()
    line = (
        f"\n- **[path-to-agent-memory-fleet]** = `{path_value}`"
        f"  <!-- overlay-path-def {_PATH_DEF_UUID} -->\n"
    )
    with claude_md.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
    return f"  Registered [path-to-agent-memory-fleet] = {path_value}"


def _register_layer_access(claude_md: Path, layer: str, uuid: str) -> str:
    """Define ``[<LAYER>-ACCESS]`` / ``[<LAYER>-MCP-URL]`` in the global CLAUDE.md (idempotent).

    How the fleet is reached: `markdown` for installed commands, `mcp` for procedures served over
    a connected server. A caller reads the target layer's declaration, so each layer's own
    installer writes it. UUID-guarded so re-runs never duplicate the line.
    """
    if not claude_md.is_file():
        return (
            f"  NOTE: {claude_md} not found - could not register\n"
            f"        [{layer}-ACCESS]. Run the memory-core setup first, then re-run."
        )
    marker = f"**[{layer}-ACCESS]**"
    if marker in claude_md.read_text(encoding="utf-8"):
        return f"  [{layer}-ACCESS] already registered in CLAUDE.md - skipped."

    mode = os.environ.get(f"{layer}_ACCESS", "markdown")
    url = os.environ.get(f"{layer}_MCP_URL", "<unset>")
    label = layer.lower()
    block = (
        "\n"
        f"- **[{layer}-ACCESS]** = `{mode}` (which form the {label} layer this machine uses: "
        "`markdown` for the installed commands/skills, `mcp` for the procedures served over a "
        "connected server)\n"
        f"- **[{layer}-MCP-URL]** = `{url}` (the endpoint the served {label} layer is reached at)"
        f"  <!-- overlay-{label}-access-def {uuid} -->\n"
    )
    with claude_md.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    return f"  Registered [{layer}-ACCESS] = {mode} ([{layer}-MCP-URL] = {url})"


def install(
    target_dir: Path | str,
    root: Path | str = _ROOT,
    output_dir: Path | str | None = None,
) -> tuple[list[str], int]:
    """Compile the overlay command set and install it into ``target_dir``.

    Returns ``(installed_command_names, removed_count)``.
    """
    root = Path(root)
    target_dir = Path(target_dir)
    output_dir = Path(output_dir) if output_dir else root / "output"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Install exactly what this run produced, rather than globbing the output dir — no stale
    # file from an earlier compile can slip into the installed set.
    reports = _cc.compile_all(root, output_dir, verbose=False)

    removed = _cleanup(
        target_dir,
        target_dir / _MANIFEST_NAME,
        [target_dir / name for name in _SIBLING_MANIFEST_NAMES],
    )

    installed: list[str] = []
    manifest_lines: list[str] = []
    for report in reports:
        shutil.copyfile(report.out_path, target_dir / report.out_path.name)
        installed.append(report.name)
        manifest_lines.append(report.out_path.name)

    (target_dir / _MANIFEST_NAME).write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8", newline="\n"
    )
    return installed, removed


def main(argv: list[str] | None = None) -> int:
    target = Path(
        os.environ.get("AGENT_MEMORY_TARGET_DIR") or Path.home() / ".claude" / "commands"
    )

    print("=== Setup agent-memory-fleet OVERLAY Slash Commands ===\n")
    print(f"Source (overlay): {_ROOT / 'output'}")
    print(f"Target:           {target}\n")

    if not (_ROOT / "procedures").is_dir():
        print(f"Error: overlay procedures directory not found: {_ROOT / 'procedures'}")
        return 1

    installed, removed = install(target)

    if removed:
        print("Cleaning up previously installed overlay commands...")
        print(f"  Removed {removed} stale overlay commands\n")
    if not installed:
        print("Error: no procedures compiled — nothing installed.")
        return 1

    print(f"Successfully installed {len(installed)} fleet procedures!\n")
    print(_register_overlay_path(Path.home() / ".claude" / "CLAUDE.md", _ROOT))
    print(
        _register_layer_access(
            Path.home() / ".claude" / "CLAUDE.md", "FLEET", _FLEET_ACCESS_UUID
        )
    )
    print("\nInstalled overlay commands:")
    for name in installed:
        print(f"  /{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
