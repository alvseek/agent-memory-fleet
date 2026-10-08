"""compile-procedures — component inlining and template resolution.

Lives beside the tool it tests. The tool (``setup-scripts/compile-procedures.py``) has a
hyphen in its name, so it is loaded by file path rather than imported as a module.

Behaviour is asserted against **synthetic** repos built in ``tmp_path``: the real
``procedures/`` tree changes constantly, so content-coupled assertions would break for
reasons that have nothing to do with the compiler. The real tree is checked only for the
properties that must hold whatever it contains.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = ROOT / "setup-scripts" / "compile-procedures.py"

# The installer registers this in the global instructions file, so a reference rooted at it
# resolves at run time. It is what makes leaving a template path in the output safe.
_PLACEHOLDER = "[path-to-agent-memory-fleet]"

_spec = importlib.util.spec_from_file_location("overlay_compile", _SCRIPT)
cc = importlib.util.module_from_spec(_spec)
sys.modules["overlay_compile"] = cc  # dataclass field resolution needs the module registered
_spec.loader.exec_module(cc)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _mkrepo(
    root: Path,
    procedures: dict[str, str],
    components: dict[str, str] | None = None,
    templates: dict[str, str] | None = None,
    plan_templates: dict[str, str] | None = None,
) -> Path:
    """Build a minimal overlay tree so a behaviour can be asserted in isolation."""
    for name, text in procedures.items():
        _write(root / "procedures" / f"{name}.md", text)
    for name, text in (components or {}).items():
        _write(root / "components" / f"{name}.md", text)
    for name, text in (templates or {}).items():
        _write(root / "templates" / f"{name}.md", text)
    for name, text in (plan_templates or {}).items():
        _write(root / "plan-templates" / f"{name}.md", text)
    return root


def _compile(repo: Path, out: Path) -> list:
    return cc.compile_all(repo, out, verbose=False)


def _first_text(repo: Path, out: Path) -> str:
    """Compiled text of the single procedure in a synthetic repo."""
    return _compile(repo, out)[0].out_path.read_text(encoding="utf-8")


# A component document: header block, `---` rule, then the inlinable body.
_COMPONENT = "# The Component\n\n*Not a standalone skill.*\n\n---\n\nBODY LINE ONE\nBODY LINE TWO\n"


# --------------------------------------------------------------------------- real tree


def test_every_procedure_compiles(tmp_path: Path) -> None:
    reports = cc.compile_all(ROOT, tmp_path, verbose=False)
    sources = {p.stem for p in (ROOT / "procedures").glob("*.md")}
    assert {r.name for r in reports} == sources
    assert sources  # the tree is not empty
    for r in reports:
        assert r.out_path.is_file()


def test_real_tree_has_no_unresolved_references(tmp_path: Path) -> None:
    """The condition `--strict` enforces in CI: every reference resolves."""
    reports = cc.compile_all(ROOT, tmp_path, verbose=False)
    unresolved = {
        r.name: (r.missing_components, r.missing_templates) for r in reports if not r.clean
    }
    assert unresolved == {}


def test_compiled_output_is_self_contained(tmp_path: Path) -> None:
    """An installed command must never *link* to a file the agent cannot reach.

    Components are inlined, so no component link may survive. Template references DO
    survive — the agent copies a template by path, so inlining one would hand over the
    content and take away the source — but only in placeholder-rooted form, which the
    installer registers and the agent can resolve. A bare relative dev-time path could not.

    Asserted as reference forms rather than bare substrings: procedure prose legitimately
    contains example paths like ``src/components/Modal.tsx``, which are not references.
    """
    for report in cc.compile_all(ROOT, tmp_path, verbose=False):
        text = report.out_path.read_text(encoding="utf-8")
        assert not cc._COMPONENT_LINK.search(text), report.name
        for line in text.splitlines():
            for m in cc._TPL_REF.finditer(line):
                assert line[: m.start()].endswith(_PLACEHOLDER), f"{report.name}: {line}"


def test_output_is_lf_only(tmp_path: Path) -> None:
    for report in cc.compile_all(ROOT, tmp_path, verbose=False):
        assert b"\r" not in report.out_path.read_bytes(), report.name


def test_compile_is_deterministic(tmp_path: Path) -> None:
    first = {r.name: r.out_path.read_bytes() for r in _compile(ROOT, tmp_path / "a")}
    second = {r.name: r.out_path.read_bytes() for r in _compile(ROOT, tmp_path / "b")}
    assert first == second


# ---------------------------------------------------------------- component inlining


def test_component_is_inlined_at_its_reference_point(tmp_path: Path) -> None:
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Intro.\n\nDo [The Thing](x/components/comp-one.md) now.\n\nOutro.\n"},
        components={"comp-one": _COMPONENT},
    )
    reports = _compile(repo, tmp_path / "out")
    text = reports[0].out_path.read_text(encoding="utf-8")

    assert "Do The Thing now." in text  # link replaced by its label
    assert "BODY LINE ONE" in text  # body inserted
    ref, body, outro = text.index("Do The Thing"), text.index("BODY LINE ONE"), text.index("Outro.")
    assert ref < body < outro  # inserted at the reference point, not appended
    assert "*Not a standalone skill.*" not in text  # header above the `---` rule is dropped
    assert reports[0].components == ["comp-one"]


def test_other_links_on_the_line_survive(tmp_path: Path) -> None:
    """Only component links are de-linked.

    Regression: the original shell compiler ran a global de-link over any line holding a
    component reference, which silently flattened a real in-doc anchor into plain text.
    """
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Use [Comp](x/components/comp-one.md) and see [Docs](#docs) below.\n"},
        components={"comp-one": _COMPONENT},
    )
    assert "Use Comp and see [Docs](#docs) below." in _first_text(repo, tmp_path / "out")


def test_prose_mention_of_a_component_path_is_not_a_reference(tmp_path: Path) -> None:
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Components live in components/comp-one.md on disk.\n"},
        components={"comp-one": _COMPONENT},
    )
    report = cc.compile_all(repo, tmp_path / "out", verbose=False)[0]
    assert report.components == []
    assert "BODY LINE ONE" not in report.out_path.read_text(encoding="utf-8")


def test_missing_component_is_reported_not_silent(tmp_path: Path) -> None:
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Follow the [Gone](x/components/nope.md).\n"},
        components={},
    )
    report = cc.compile_all(repo, tmp_path / "out", verbose=False)[0]
    assert report.missing_components == ["nope"]
    assert not report.clean  # this is what `--strict` fails CI on


# ----------------------------------------------------------------------- templates


def test_templates_are_resolved_but_never_inlined(tmp_path: Path) -> None:
    """Discovery still walks templates transitively; nothing is copied into the output.

    A template is an artifact the procedure *copies to disk*, so the agent needs its path.
    Inlining one hands over the content and takes away the source — which is exactly how
    ``cp {source} ...`` ended up with nothing to substitute.
    """
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Shape it per [the plan](x/plan-templates/outer-template.md).\n"},
        plan_templates={
            "outer-template": "# Outer\n\nOUTER BODY, see [inner](y/templates/inner-template.md).\n"
        },
        templates={"inner-template": "# Inner\n\nINNER BODY\n"},
    )
    report = _compile(repo, tmp_path / "out")[0]
    text = report.out_path.read_text(encoding="utf-8")

    assert report.templates == ["outer-template", "inner-template"]  # discovery order, transitive
    assert "Shape it per [the plan](x/plan-templates/outer-template.md)." in text  # untouched
    assert "## Templates" not in text  # the appendix is gone
    assert "OUTER BODY" not in text and "INNER BODY" not in text  # no body reaches the output


def test_backtick_code_path_template_reference_is_left_alone(tmp_path: Path) -> None:
    ref = "`[path-to-agent-memory-fleet]/templates/tpl-one.md`"
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": f"See {ref} here.\n"},
        templates={"tpl-one": "# T1\n\nT1 BODY\n"},
    )
    assert f"See {ref} here." in _first_text(repo, tmp_path / "out")


def test_anchored_template_reference_keeps_its_path_and_anchor(tmp_path: Path) -> None:
    ref = "x/templates/tpl-one.md#some-section"
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": f"Jump to [a section]({ref}).\n"},
        templates={"tpl-one": "# T1\n\nT1 BODY\n"},
    )
    assert f"Jump to [a section]({ref})." in _first_text(repo, tmp_path / "out")


def test_missing_template_is_reported(tmp_path: Path) -> None:
    """A dangling template path is the one failure this stage still exists to catch."""
    repo = _mkrepo(
        tmp_path / "repo",
        procedures={"p": "Per [gone](x/templates/gone.md).\n"},
        templates={},
    )
    report = cc.compile_all(repo, tmp_path / "out", verbose=False)[0]
    assert report.missing_templates == ["gone"]
    assert not report.clean  # this is what `--strict` fails CI on


def test_procedure_with_no_references_is_copied_verbatim(tmp_path: Path) -> None:
    repo = _mkrepo(tmp_path / "repo", procedures={"p": "Nothing to inline here.\n"})
    report = cc.compile_all(repo, tmp_path / "out", verbose=False)[0]
    assert report.templates == []
    assert report.out_path.read_text(encoding="utf-8") == "Nothing to inline here.\n"


# ----------------------------------------------------------------------------- CLI


def test_strict_passes_on_the_real_tree(tmp_path: Path) -> None:
    assert cc.main(["--strict", "--quiet", "--out", str(tmp_path)]) == 0
