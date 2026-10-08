"""Compile ``procedures/*.md`` into self-contained ``output/*.md``.

Produces install-ready commands with NO references to the overlay's own component/template
files, so an installed slash command never points at a path the agent cannot reach:

- **Components** (``[label](.../components/X.md)``) are INLINED at the reference point — the
  link becomes its label text and the component body is inserted right after, so caller
  params written into the sentence survive.
- **Templates are NOT inlined.** Every template in this repo is *copied to disk* by the
  procedure that references it, so what the agent needs is a path, not the text: a plan
  template becomes a plan file, a doc template becomes a doc. Inlining one hands over the
  content and takes away the source, which is why ``cp {source} ...`` had nothing to
  substitute. References are left exactly as authored and resolve at run time.
- **Runtime refs are left alone**: ``[AGENT-MEMORY-PATH]/...`` (where memory lives),
  ``[path-to-agent-memory-coding-skill]/fleet-scripts/*.sh`` (executables the agent runs),
  and template paths under ``plan-templates/`` and ``templates/``.

Templates are still *resolved* at compile time: a reference naming a template that does not
exist is reported, and fails the build under ``--strict``. A dangling path is the one failure
this stage still exists to catch.

Output name == source name, so ``/wait-options`` stays ``/wait-options``.

This replaces the former ``compile-procedures.sh``. The shell version spawned ~580 short-lived
processes (awk/sed/grep/mktemp/basename per file); under Git-Bash on Windows each spawn costs
~0.27s — MSYS2 fork emulation on top of real-time AV scanning — so a 34s job took 2m38s of wall
clock. Python does the same work in one process.

Cross-platform: run directly on macOS/Linux, or via the ``.bat`` wrapper on Windows.

Usage: python setup-scripts/compile-procedures.py [--out DIR] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Repo root (this script lives at setup-scripts/compile-procedures.py).
_ROOT = Path(__file__).resolve().parents[1]

_TEMPLATE_DIRNAMES = ("plan-templates", "templates")

# A component reference: `[label](<any-prefix>/components/<name>.md)`. The path prefix is free
# (a relative dev-time link and a placeholder-rooted one both resolve to the same component) and
# the closing paren is required, so a bare mention of a components/ path in prose is not a
# reference. Group 1 is the label that replaces the link; group 2 is the component name.
_COMPONENT_LINK = re.compile(r"\[([^\]]*)\]\([^)\n]*/components/([a-z-]+)\.md\)")
# A template reference anywhere (link or backtick code-path form) → its bare name.
_TPL_REF = re.compile(r"/(?:plan-templates|templates)/([a-z-]+)\.md")


@dataclass
class Report:
    """What one compiled procedure pulled in, and anything it could not resolve."""

    name: str
    out_path: Path
    components: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    missing_components: list[str] = field(default_factory=list)
    missing_templates: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.missing_components and not self.missing_templates


def _read(path: Path) -> str:
    """Read a source file without newline translation (every file in this repo is LF)."""
    return path.read_text(encoding="utf-8")


def _lines(text: str) -> list[str]:
    """Split into lines the way awk does — trailing newline yields no extra empty record.

    Deliberately not ``str.splitlines()``: that also splits on \\v, \\f and U+2028, which
    appear inside procedure prose and would silently introduce line breaks awk never made.
    """
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def _emit(lines: list[str]) -> str:
    """Join printed lines the way awk's ``print`` does — one trailing newline each."""
    return "".join(line + "\n" for line in lines)


def component_body(text: str) -> list[str]:
    """The inlinable body of a component: everything after its first standalone ``---`` rule.

    A component opens with a header block (title + a note that it is a component, not a
    standalone skill) separated from the body by that rule. A component with no such rule
    contributes nothing — same as the shell, which only started printing once it had seen one.
    """
    out: list[str] = []
    started = False
    for line in _lines(text):
        if started:
            out.append(line)
        if re.fullmatch(r"---[ \t]*", line):
            started = True
    return out


def find_template(name: str, root: Path) -> Path | None:
    """Locate a template by bare name across the template dirs, in precedence order."""
    for dirname in _TEMPLATE_DIRNAMES:
        candidate = root / dirname / f"{name}.md"
        if candidate.is_file():
            return candidate
    return None


def template_names_in(text: str) -> list[str]:
    """Bare template names referenced in ``text`` — unique, in order of first appearance."""
    seen: dict[str, None] = {}
    for name in _TPL_REF.findall(text):
        seen.setdefault(name, None)
    return list(seen)


def inline_components(text: str, components_dir: Path) -> tuple[str, list[str], list[str]]:
    """Inline every component reference at its reference point.

    Returns ``(text, used, missing)``. On a referencing line each component link is replaced by
    its label text — so caller params written into the sentence survive — and the component body
    is inserted right after, preceded by a blank line.

    Only *component* links are de-linked. Any other link on the same line is left intact: the
    shell de-linked every link on the line, which silently flattened a real in-doc anchor
    (``[Templates](#templates)``) into plain text in the installed command.

    A missing component contributes no body — faithful to the shell, which failed its read
    silently — but its name is returned in ``missing`` so the caller can surface it rather
    than letting the reference vanish unnoticed.
    """
    out: list[str] = []
    used: list[str] = []
    missing: list[str] = []

    for line in _lines(text):
        matches = _COMPONENT_LINK.findall(line)
        if not matches:
            out.append(line)
            continue

        out.append(_COMPONENT_LINK.sub(r"\1", line))
        for _label, name in matches:
            out.append("")
            path = components_dir / f"{name}.md"
            if path.is_file():
                used.append(name)
                out.extend(component_body(_read(path)))
            else:
                missing.append(name)

    return _emit(out), used, missing


def collect_templates(text: str, root: Path) -> tuple[list[str], list[str]]:
    """Template names referenced by ``text``, collected transitively in discovery order.

    Returns ``(order, missing)`` — ``missing`` names still get an appendix placeholder, so an
    unresolved template is visible in the output rather than silently dropped.
    """
    order: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    queue: list[str] = []

    for name in template_names_in(text):
        if name not in seen:
            seen.add(name)
            order.append(name)
            queue.append(name)

    index = 0
    while index < len(queue):
        name = queue[index]
        index += 1
        path = find_template(name, root)
        if path is None:
            missing.append(name)
            continue
        for nested in template_names_in(_read(path)):
            if nested not in seen:
                seen.add(nested)
                order.append(nested)
                queue.append(nested)

    return order, missing


def compile_one(src: Path, out_dir: Path, root: Path) -> Report:
    """Compile a single procedure into ``out_dir``."""
    report = Report(name=src.stem, out_path=out_dir / src.name)

    text, used, missing = inline_components(_read(src), root / "components")
    report.components = used
    report.missing_components = missing

    # Templates are resolved but never inlined — the agent copies them by path.
    order, missing_templates = collect_templates(text, root)
    report.templates = order
    report.missing_templates = missing_templates

    report.out_path.write_text(text, encoding="utf-8", newline="\n")
    return report


def compile_all(
    root: Path | str = _ROOT,
    out_dir: Path | str | None = None,
    verbose: bool = True,
) -> list[Report]:
    """Compile every procedure. Returns one ``Report`` per compiled file, in name order."""
    root = Path(root)
    proc_dir = root / "procedures"
    out_dir = Path(out_dir) if out_dir else root / "output"

    if not proc_dir.is_dir():
        raise FileNotFoundError(f"procedures/ not found at {proc_dir}")

    sources = sorted(proc_dir.glob("*.md"))
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(
            f"Compiling {len(sources)} procedures "
            f"(inlining components, resolving templates) -> {out_dir} ..."
        )

    reports: list[Report] = []
    for i, src in enumerate(sources, start=1):
        if verbose:
            print(f"  [{i}/{len(sources)}] {src.name}")
        reports.append(compile_one(src, out_dir, root))
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", help="output directory (default: <repo>/output)")
    parser.add_argument("--quiet", action="store_true", help="only print the summary")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any component or template reference is unresolved (for CI)",
    )
    args = parser.parse_args(argv)

    reports = compile_all(_ROOT, args.out, verbose=not args.quiet)
    out_dir = Path(args.out) if args.out else _ROOT / "output"
    print(f"Compiled {len(reports)} procedures -> {out_dir}")

    # Unresolved references never fail silently — the shell dropped missing components with no
    # trace, which is how a broken reference could ship inside an installed command.
    unresolved = [r for r in reports if not r.clean]
    for r in unresolved:
        for name in r.missing_components:
            print(f"  WARNING: {r.name}: component not found: {name}.md", file=sys.stderr)
        for name in r.missing_templates:
            print(f"  WARNING: {r.name}: template not found: {name}.md", file=sys.stderr)
    if unresolved:
        print(f"  {len(unresolved)} procedure(s) with unresolved references.", file=sys.stderr)
        if args.strict:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
