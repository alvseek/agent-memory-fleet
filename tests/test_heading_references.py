"""Prose references to a `## Heading` must point at a heading that exists.

`compile-procedures.py --strict` verifies *link* references — components and templates.
It cannot see a sentence like "check `## WAIT Options Scope` above", so a heading can be
renamed or removed while every automated check stays green and the instruction quietly
points at nothing.

That is not hypothetical: on 2026-08-15 the wizard procedures had their altitude guidance
folded from a `## WAIT Options Scope` section into their opening prose, and two documents
were left telling agents to go read a heading that no longer existed anywhere in the repo.
ruff, the full suite, and `--strict` all passed.

Checked across the authored docs only. A handful of referenced headings genuinely live
outside this repo — they are allow-listed below with the reason, so the list stays a
statement about ownership rather than a place to silence failures.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_AUTHORED_DIRS = ("procedures", "templates")

# A backticked prose reference: `## Some Heading`
_REFERENCE = re.compile(r"`#{1,4}\s+([^`\n]+?)\s*`")
# A heading definition, tolerating the bold form used by the plan templates: ## **NAME**
_DEFINITION = re.compile(r"^#{1,4}\s+\*{0,2}\s*(.+?)\s*\*{0,2}\s*$")

# Headings referenced here but owned elsewhere. Each entry states who owns it.
_DEFINED_ELSEWHERE = {
    # /run-qa-test writes this into whichever plan invoked it; the caller may also name
    # its own section. It is a write target in a foreign artifact, not a section here.
    "runtime verification",
    # Sections of the central agent-memory-index.md, which lives in the agent-memory
    # store rather than this repo. /localize-context maintains them there.
    "localized projects",
    "core knowledge base",
}

# Many procedures quote a heading they will *write*, not one they expect to find:
# `## [PROJECT] Project Context`, `## R/I/A/O category:`, `## fixture: {stage} …`.
# Those are output specifications and have no target to resolve against. A placeholder
# or a trailing colon is what distinguishes a heading being described from one being
# pointed at — without this, the check reports 16 non-problems and gets ignored.
_IS_A_TEMPLATE = re.compile(r"[\[\]{}]|\.\.\.|…|:\s*$")


def _authored_files() -> list[Path]:
    dirs = [ROOT / d for d in _AUTHORED_DIRS if (ROOT / d).is_dir()]
    return sorted(p for d in dirs for p in d.rglob("*.md"))


def _defined_headings(files: list[Path]) -> set[str]:
    found: set[str] = set()
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _DEFINITION.match(line)
            if match:
                found.add(match.group(1).strip().lower())
    return found


def test_every_referenced_heading_is_defined() -> None:
    files = _authored_files()
    assert files, "no authored docs found - the globs are wrong, not the docs"

    defined = _defined_headings(files) | _DEFINED_ELSEWHERE
    dangling: list[str] = []

    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue  # a heading defining itself is not a reference to one
            for name in _REFERENCE.findall(line):
                if _IS_A_TEMPLATE.search(name):
                    continue  # a heading being specified, not one being pointed at
                if name.strip().lower() not in defined:
                    rel = path.relative_to(ROOT).as_posix()
                    dangling.append(f"{rel}:{number} -> `## {name}`")

    assert not dangling, "prose points at headings that do not exist:\n  " + "\n  ".join(dangling)


def test_the_check_catches_a_removed_heading(tmp_path: Path) -> None:
    """Mutation guard: prove the assertion above actually bites.

    Without this, a regex that silently matches nothing would keep the suite green forever
    while checking exactly nothing — the failure mode that motivated the whole file.
    """
    doc = tmp_path / "proc.md"
    doc.write_text("Check `## Gone Section` before starting.\n", encoding="utf-8")

    defined = _defined_headings([doc])
    assert defined == set(), "a file with no headings should define none"

    referenced = _REFERENCE.findall(doc.read_text(encoding="utf-8"))
    assert referenced == ["Gone Section"], "the reference regex missed a plain reference"
    assert "gone section" not in defined


def test_a_heading_being_specified_is_not_treated_as_a_reference() -> None:
    """Placeholders and prefix patterns describe output, so they have nothing to resolve."""
    specified = (
        "## [PROJECT] Project Context",
        "## R/I/A/O category:",
        "## fixture: {stage} …",
    )
    for described in specified:
        name = _REFERENCE.findall(f"write a `{described}` block")[0]
        assert _IS_A_TEMPLATE.search(name), f"{described} should read as a specification"

    for pointed_at in ("## QA HANDOFF", "## Inherited Context"):
        name = _REFERENCE.findall(f"see `{pointed_at}` above")[0]
        assert not _IS_A_TEMPLATE.search(name), f"{pointed_at} should read as a reference"


def test_bold_and_plain_heading_forms_both_count_as_defined(tmp_path: Path) -> None:
    """The plan templates write `## **QA HANDOFF**`; procedures reference `## QA HANDOFF`.

    An earlier hand-rolled version of this check missed the bold form and reported three
    false positives, which is how a noisy check trains you to ignore it.
    """
    doc = tmp_path / "tpl.md"
    doc.write_text("## **QA HANDOFF**\n\n## Plain Heading\n", encoding="utf-8")

    defined = _defined_headings([doc])
    assert "qa handoff" in defined
    assert "plain heading" in defined
