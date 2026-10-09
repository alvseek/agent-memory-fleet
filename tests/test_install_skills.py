"""Tests for install-skills.py — the shared Codex / Antigravity skill installer.

Loaded by file path (hyphenated name). Every ``install()`` call is pointed at tmp dirs, so the
real ``~/.agents/skills``, ``~/.gemini/config/skills`` and the shared ``output/`` are never
touched — and ``run()`` is never called, since it also appends to a global instructions file.

The frontmatter tests carry the weight here. A skill's ``description`` is derived from prose
nobody writes with YAML in mind, and unparseable frontmatter does not raise anywhere we would
see it — the platform simply never loads the skill. Three procedures already contain a bare
``": "`` in their opening sentence, so this is a defect that existed rather than one imagined.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = ROOT / "setup-scripts" / "install-skills.py"

_spec = importlib.util.spec_from_file_location("overlay_install_skills", _SCRIPT)
sk = importlib.util.module_from_spec(_spec)
sys.modules["overlay_install_skills"] = sk
_spec.loader.exec_module(sk)

_MANIFEST = ".agent-memory-fleet-codex-manifest"
_SIBLING_MANIFESTS = [".agent-memory-codex-manifest", ".agent-memory-project-codex-manifest"]

# Antigravity documents 1024; staying inside the smaller published cap keeps one emitter
# correct for both platforms.
_DESCRIPTION_LIMIT = 1024

# A YAML double-quoted scalar: quotes and backslashes escaped, nothing else bare.
_QUOTED_SCALAR = re.compile(r'^description: "(?:[^"\\]|\\.)*"$')

# Fleet procedures every healthy tree carries.
_KNOWN = {"setup-fleet", "load-fleet", "ask-agent", "delegate-agent"}


def _install(tmp_path: Path):
    target = tmp_path / "skills"
    out = tmp_path / "out"
    installed, removed = sk.install(
        target, _MANIFEST, _SIBLING_MANIFESTS, root=ROOT, output_dir=out
    )
    return target, out, installed, removed


def test_folder_prefix_is_the_overlay_prefix() -> None:
    """The overlay's folder prefix must differ from the memory core's ``agent-memory-`` one.

    Both installers write into the same skills directory, so sharing a prefix would let a
    same-named core procedure silently clobber an overlay folder (manifests guard deletion,
    not overwrite). Pinned literally so a well-meaning "consistency" rename fails loudly.
    """
    assert sk.FOLDER_PREFIX == "agent-fleet-"


def _frontmatter_lines(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{skill_md}: no opening frontmatter fence"
    return text.split("---\n")[1].splitlines()


def test_installs_the_full_skill_set(tmp_path: Path) -> None:
    target, _, installed, _ = _install(tmp_path)

    assert _KNOWN <= set(installed)
    for name in installed:
        assert (target / f"{sk.FOLDER_PREFIX}{name}" / "SKILL.md").is_file()

    manifest = (target / _MANIFEST).read_text(encoding="utf-8").split()
    assert sorted(manifest) == sorted(f"{sk.FOLDER_PREFIX}{n}" for n in installed)


def test_skill_body_is_the_compiled_procedure_verbatim(tmp_path: Path) -> None:
    """A skill and a slash command must be the same instruction.

    If the body were transformed per platform, a procedure would behave differently depending on
    which tool loaded it — which is the class of bug the compile step exists to prevent.
    """
    target, out, installed, _ = _install(tmp_path)
    for name in installed:
        skill = (target / f"{sk.FOLDER_PREFIX}{name}" / "SKILL.md").read_text(encoding="utf-8")
        compiled = (out / f"{name}.md").read_text(encoding="utf-8")
        assert skill.endswith(compiled), name


def test_every_description_is_a_quoted_yaml_scalar(tmp_path: Path) -> None:
    target, _, installed, _ = _install(tmp_path)
    for name in installed:
        lines = _frontmatter_lines(target / f"{sk.FOLDER_PREFIX}{name}" / "SKILL.md")
        desc = [ln for ln in lines if ln.startswith("description: ")]
        assert len(desc) == 1, name
        assert _QUOTED_SCALAR.match(desc[0]), f"{name}: unquoted or badly escaped: {desc[0]}"


def test_every_skill_declares_its_own_name(tmp_path: Path) -> None:
    target, _, installed, _ = _install(tmp_path)
    for name in installed:
        lines = _frontmatter_lines(target / f"{sk.FOLDER_PREFIX}{name}" / "SKILL.md")
        assert f"name: {name}" in lines, name


def test_descriptions_stay_within_the_platform_cap(tmp_path: Path) -> None:
    target, _, installed, _ = _install(tmp_path)
    for name in installed:
        lines = _frontmatter_lines(target / f"{sk.FOLDER_PREFIX}{name}" / "SKILL.md")
        desc = next(ln for ln in lines if ln.startswith("description: "))
        # measured on the scalar's content, not the emitted line
        assert len(desc) - len('description: ""') <= _DESCRIPTION_LIMIT, name


def test_yaml_scalar_escapes_hostile_input() -> None:
    """The negative control for the frontmatter tests above.

    Without escaping, a colon-space in a derived description silently produces frontmatter no
    parser accepts. ``generate-readme`` really does open with "full name: 7 Questions Framework
    README", so this is the shape that occurs, not an invented one.
    """
    assert sk._yaml_scalar("full name: 7Q README") == '"full name: 7Q README"'
    assert sk._yaml_scalar('say "hi"') == '"say \\"hi\\""'
    assert sk._yaml_scalar(r"a\b") == '"a\\\\b"'
    # a plain (unquoted) emission of the first case is what this guards against
    assert ": " in "description: full name: 7Q README".removeprefix("description: ")


def test_reinstall_cleans_stale_but_never_a_sibling_skill(tmp_path: Path) -> None:
    """Order-independence: the core and overlay installers share one skills directory.

    A stale overlay entry — a procedure that moved core<->overlay in an earlier session — must
    not delete the skill the core installer now owns.
    """
    target, out, first, _ = _install(tmp_path)

    # a skill from a prior overlay run that no longer exists must be removed on reinstall
    stale = target / f"{sk.FOLDER_PREFIX}gone-procedure"
    stale.mkdir()
    (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
    manifest = target / _MANIFEST
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + f"{stale.name}\n", encoding="utf-8"
    )

    # one the core now claims must survive, even though the overlay manifest still lists it
    shared = target / f"{sk.FOLDER_PREFIX}moved-to-core"
    shared.mkdir()
    (shared / "SKILL.md").write_text("core-owned\n", encoding="utf-8")
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + f"{shared.name}\n", encoding="utf-8"
    )
    (target / _SIBLING_MANIFESTS[0]).write_text(f"{shared.name}\n", encoding="utf-8")

    second, removed = sk.install(
        target, _MANIFEST, _SIBLING_MANIFESTS, root=ROOT, output_dir=out
    )

    assert not stale.exists(), "stale overlay skill was not cleaned up"
    assert shared.is_dir(), "cleanup deleted a skill the sibling manifest claims"
    assert (shared / "SKILL.md").read_text(encoding="utf-8") == "core-owned\n"
    # cleanup clears the whole prior manifest before reinstalling, so the count is every
    # previously-installed skill plus the stale one, with the sibling-claimed one skipped
    assert removed == len(first) + 1
    assert sorted(second) == sorted(first)


def test_any_sibling_manifest_protects_its_skills(tmp_path: Path) -> None:
    """A name claimed by ANY sibling (here the coding overlay) survives a fleet reinstall."""
    target, out, _first, _ = _install(tmp_path)

    coding_owned = target / f"{sk.FOLDER_PREFIX}coding-owned"
    coding_owned.mkdir()
    (coding_owned / "SKILL.md").write_text("coding\n", encoding="utf-8")
    manifest = target / _MANIFEST
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + f"{coding_owned.name}\n", encoding="utf-8"
    )
    (target / _SIBLING_MANIFESTS[1]).write_text(f"{coding_owned.name}\n", encoding="utf-8")

    sk.install(target, _MANIFEST, _SIBLING_MANIFESTS, root=ROOT, output_dir=out)
    assert coding_owned.is_dir(), "cleanup deleted a skill a second sibling claims"


def test_fleet_layer_access_registration_is_idempotent(tmp_path: Path) -> None:
    """The fleet-layer declaration is written once, uuid-guarded, even across re-runs."""
    instructions = tmp_path / "AGENTS.md"
    instructions.write_text("# Global instructions\n", encoding="utf-8", newline="\n")

    first = sk.register_layer_access(instructions, "FLEET", sk._FLEET_ACCESS_UUID)
    body = instructions.read_text(encoding="utf-8")
    assert "Registered" in first
    assert "**[FLEET-ACCESS]**" in body
    assert body.count(sk._FLEET_ACCESS_UUID) == 1

    second = sk.register_layer_access(instructions, "FLEET", sk._FLEET_ACCESS_UUID)
    assert "already registered" in second
    assert instructions.read_text(encoding="utf-8").count(sk._FLEET_ACCESS_UUID) == 1
