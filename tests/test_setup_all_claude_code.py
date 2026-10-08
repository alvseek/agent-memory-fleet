"""Tests for setup-all-claude-code.py — the Python slash-command installer.

Loaded by file path (hyphenated name). Every ``install()`` call is pointed at tmp dirs, so the
real ``~/.claude/commands`` and the shared ``output/`` are never touched — and ``main()`` is
never called, since it also appends to the global CLAUDE.md.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = ROOT / "setup-scripts" / "setup-all-claude-code.py"

_spec = importlib.util.spec_from_file_location("overlay_setup", _SCRIPT)
si = importlib.util.module_from_spec(_spec)
sys.modules["overlay_setup"] = si
_spec.loader.exec_module(si)

# the installer loads the compiler itself; reuse that instance so "self-contained" is asserted
# with the compiler's own reference patterns, with no dependence on test import order.
cc = si._cc

_MANIFEST = ".agent-memory-fleet-manifest"
_SIBLING_MANIFEST = ".agent-memory-manifest"

# registered by the installer in the global instructions file, so a reference rooted at it
# resolves at run time — which is what makes an installed template path safe.
_PLACEHOLDER = "[path-to-agent-memory-fleet]"

# Fleet commands every healthy tree carries. Populated in Phase 4 of the extraction plan;
# empty at scaffold time so the tooling tests run green first.
_KNOWN: set[str] = set()


def test_installs_the_full_command_set(tmp_path: Path) -> None:
    target = tmp_path / "commands"
    installed, _ = si.install(target, root=ROOT, output_dir=tmp_path / "out")

    assert _KNOWN <= set(installed)
    for name in installed:
        assert (target / f"{name}.md").is_file()
    manifest = (target / _MANIFEST).read_text(encoding="utf-8").split()
    assert sorted(manifest) == sorted(f"{n}.md" for n in installed)


def test_installed_command_matches_the_compiled_output(tmp_path: Path) -> None:
    target = tmp_path / "commands"
    out = tmp_path / "out"
    installed, _ = si.install(target, root=ROOT, output_dir=out)
    for name in installed:
        assert (target / f"{name}.md").read_bytes() == (out / f"{name}.md").read_bytes()


def test_installed_command_carries_no_dev_time_reference(tmp_path: Path) -> None:
    """The installed command is the compiled one — no component link, no unrooted path.

    A template path is not a dev-time reference: the agent copies templates by path, and the
    installer registers ``[path-to-agent-memory-fleet]`` so a rooted one resolves. An
    *unrooted* template path would not, which is what this checks for.
    """
    target = tmp_path / "commands"
    installed, _ = si.install(target, root=ROOT, output_dir=tmp_path / "out")
    for name in installed:
        text = (target / f"{name}.md").read_text(encoding="utf-8")
        assert not cc._COMPONENT_LINK.search(text), name
        for line in text.splitlines():
            for m in cc._TPL_REF.finditer(line):
                assert line[: m.start()].endswith(_PLACEHOLDER), f"{name}: {line}"


def test_reinstall_cleans_stale_and_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "commands"
    out = tmp_path / "out"
    first, _ = si.install(target, root=ROOT, output_dir=out)

    # a command from a prior run that no longer exists must be removed on reinstall
    (target / "gone-command.md").write_text("stale\n", encoding="utf-8")
    manifest = target / _MANIFEST
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "gone-command.md\n", encoding="utf-8"
    )

    second, removed = si.install(target, root=ROOT, output_dir=out)
    assert set(second) == set(first)
    assert not (target / "gone-command.md").exists()
    assert removed >= 1


def test_sibling_core_command_is_never_deleted(tmp_path: Path) -> None:
    """The two installers share a target dir; neither may delete the other's commands."""
    target = tmp_path / "commands"
    out = tmp_path / "out"
    si.install(target, root=ROOT, output_dir=out)

    # a command that moved overlay -> core: still in the overlay manifest, now owned by the
    # sibling core manifest, and no longer installed here — cleanup must leave it alone.
    moved = target / "moved-to-core.md"
    moved.write_text("core-owned\n", encoding="utf-8")
    manifest = target / _MANIFEST
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "moved-to-core.md\n", encoding="utf-8"
    )
    (target / _SIBLING_MANIFEST).write_text("moved-to-core.md\n", encoding="utf-8")

    si.install(target, root=ROOT, output_dir=out)
    assert moved.exists()  # protected by the sibling manifest
    assert moved.read_text(encoding="utf-8") == "core-owned\n"  # untouched


def test_any_sibling_manifest_protects_its_commands(tmp_path: Path) -> None:
    """A command claimed by ANY sibling (here the coding overlay) survives a fleet reinstall."""
    target = tmp_path / "commands"
    out = tmp_path / "out"
    si.install(target, root=ROOT, output_dir=out)

    coding_owned = target / "coding-owned.md"
    coding_owned.write_text("coding\n", encoding="utf-8")
    manifest = target / _MANIFEST
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "coding-owned.md\n", encoding="utf-8"
    )
    (target / ".agent-memory-coding-skill-manifest").write_text(
        "coding-owned.md\n", encoding="utf-8"
    )

    si.install(target, root=ROOT, output_dir=out)
    assert coding_owned.exists()  # protected by the second sibling manifest


def test_install_writes_lf_manifest(tmp_path: Path) -> None:
    target = tmp_path / "commands"
    si.install(target, root=ROOT, output_dir=tmp_path / "out")
    assert b"\r" not in (target / _MANIFEST).read_bytes()


def test_overlay_path_registration_is_idempotent(tmp_path: Path) -> None:
    """The CLAUDE.md path definition is UUID-guarded, so re-running never duplicates it."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Global instructions\n", encoding="utf-8", newline="\n")

    first = si._register_overlay_path(claude_md, ROOT)
    body = claude_md.read_text(encoding="utf-8")
    assert "Registered" in first
    assert body.count(si._PATH_DEF_UUID) == 1
    assert ROOT.as_posix() in body  # forward slashes: usable by both Windows tooling and bash

    second = si._register_overlay_path(claude_md, ROOT)
    assert "already registered" in second
    assert claude_md.read_text(encoding="utf-8").count(si._PATH_DEF_UUID) == 1


def test_missing_claude_md_is_reported_not_created(tmp_path: Path) -> None:
    claude_md = tmp_path / "absent" / "CLAUDE.md"
    message = si._register_overlay_path(claude_md, ROOT)
    assert "could not register" in message
    assert not claude_md.exists()


def test_fleet_layer_access_registration_is_idempotent(tmp_path: Path) -> None:
    """The fleet-layer declaration is written once, uuid-guarded, even across re-runs."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Global instructions\n", encoding="utf-8", newline="\n")

    first = si._register_layer_access(claude_md, "FLEET", si._FLEET_ACCESS_UUID)
    body = claude_md.read_text(encoding="utf-8")
    assert "Registered" in first
    assert "**[FLEET-ACCESS]**" in body
    assert body.count(si._FLEET_ACCESS_UUID) == 1

    second = si._register_layer_access(claude_md, "FLEET", si._FLEET_ACCESS_UUID)
    assert "already registered" in second
    assert claude_md.read_text(encoding="utf-8").count(si._FLEET_ACCESS_UUID) == 1
