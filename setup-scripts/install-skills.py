"""Shared installer for platforms that consume procedures as **Agent Skills**.

Codex and Antigravity both read a skill as a *folder* holding a ``SKILL.md`` with ``name`` and
``description`` frontmatter, so one emitter serves both and only the target directory and the
manifest name differ. The platform entry points (``setup-all-codex.py``,
``setup-all-antigravity.py``) supply those and call :func:`install`.

Why skills rather than workflows or prompts, for both platforms:

* Antigravity caps a **rules or workflow** file at 12,000 characters and is retiring workflows
  in favour of skills. Sixteen of this overlay's compiled procedures exceed that cap —
  ``pixel-wizard`` is 35k — so the workflow channel could never carry the wizards, which are
  the reason the overlay exists.
* Codex deprecated custom prompts (``~/.codex/prompts``) in favour of skills.

Skills carry no equivalent cap, and that is measured rather than inferred from the docs' silence:
on 2026-09-05 a 35,859-character ``SKILL.md`` was installed to both platforms alongside a small
control of identical shape, each ending in a distinct canary token. Both tools returned both
canaries, so the whole body arrived in each — which is why no procedure needs splitting into
``SKILL.md`` plus ``references/``.

Skills are **model-invoked**: the agent sees only ``name`` and ``description`` until it decides
a task matches, then reads the body. That makes the description the entire discovery surface,
so it is derived from each procedure's own opening sentence rather than templated — a generic
line spends the one field the agent actually reads.

Like the Claude Code installer, this compiles first and installs only what the run produced, so
no stale artifact from an earlier compile can slip into the installed set.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# Installed folders are prefixed so a skill directory shared with the memory core stays
# legible, and so each installer's manifest claims an unambiguous set. The overlay uses its own
# ``agent-fleet-`` prefix rather than the core's ``agent-memory-`` one: the two installers write
# into the same skills directory, and sharing a prefix would let a same-named procedure from
# either side silently clobber the other's folder.
FOLDER_PREFIX = "agent-fleet-"

# Both platforms cap the description; Antigravity documents 1024 characters. Staying inside the
# smaller published number keeps one emitter correct for both.
_DESCRIPTION_LIMIT = 1024

# Marks the overlay-path definition in a platform's global instructions file so re-runs never
# duplicate it. Same UUID the Claude Code installer uses — it is the same definition.
_PATH_DEF_UUID = "34ca859f-6586-4990-b729-23f834c8aaae"

# Marks the environment declarations this installer writes when the core markdown is absent.
# The guard is the [CORE-ACCESS] declaration itself, so a core-provided block is never duplicated;
# this UUID is provenance, matching the path-definition convention above.
_ENV_DEF_UUID = "669d7723-4f8e-4229-a9b2-a3f5f8edc8bf"

# Marks the fleet-layer access declaration ([FLEET-ACCESS] / [FLEET-MCP-URL]) this installer
# writes: how the fleet is reached. UUID-guarded like the others, so re-runs never duplicate it.
_FLEET_ACCESS_UUID = "40ab1e33-4da7-4687-bd20-796c1a9caf7a"

# sys.platform -> the name the compiled core memory prints on its Operating System line.
_OS_NAMES = {"win32": "Windows", "linux": "Linux", "darwin": "macOS"}

_MD_NOISE = re.compile(r"[*_`]|\[([^\]]*)\]\([^)]*\)")
_SKIP_LINE = re.compile(r"^\s*(#|[-*>|]|\d+\.|```|---)")


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


def _title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return _MD_NOISE.sub(r"\1", line[2:]).strip() or fallback
    return fallback


def _lead_sentence(text: str) -> str:
    """First real sentence of the document — its own summary of itself.

    Skips headings, list items, quotes, tables and fences, so the result is prose rather than
    a bullet fragment. Returns an empty string when the document opens with no prose at all.
    """
    for raw in text.splitlines():
        line = raw.strip()
        if not line or _SKIP_LINE.match(raw):
            continue
        line = _MD_NOISE.sub(r"\1", line).strip()
        if not line:
            continue
        # Cut at the first sentence end that is not an abbreviation-sized fragment.
        match = re.search(r"(?<=[.!?])\s", line)
        return (line[: match.start()] if match else line).strip()
    return ""


def build_description(name: str, text: str) -> str:
    """Compose a skill description: what it is, then when to reach for it.

    The trailing clause matters more than it looks — a model-invoked skill is chosen off this
    field alone, so it has to name both the command and the human words for it.
    """
    title = _title(text, name)
    lead = _lead_sentence(text)
    trigger = f"Use when the user runs /{name}, asks for the {title} procedure, or mentions {name}."
    description = f"{lead} {trigger}".strip() if lead else trigger
    if len(description) > _DESCRIPTION_LIMIT:
        keep = _DESCRIPTION_LIMIT - len(trigger) - 2
        if keep > 0:
            description = f"{lead[:keep].rstrip()}… {trigger}"
        else:
            description = trigger[:_DESCRIPTION_LIMIT]
    return description


def _yaml_scalar(value: str) -> str:
    """Emit ``value`` as a double-quoted YAML scalar.

    Always quoted, never conditionally: a description is derived from prose nobody is checking
    for YAML syntax, and a plain scalar breaks on a bare ``": "`` — which three procedures
    already contain (``generate-readme`` says "full name: 7 Questions Framework README"). The
    failure is silent, because a skill with unparseable frontmatter simply never loads.
    """
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_skill(name: str, text: str) -> str:
    """Render one ``SKILL.md``: frontmatter, then the compiled procedure unchanged.

    The body is the compiled command verbatim, so a skill and a slash command are the same
    instruction — anything else would make a procedure behave differently per platform.
    """
    description = build_description(name, text).replace("\n", " ")
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {_yaml_scalar(description)}\n"
        "---\n\n"
        "Follow this procedure exactly. Treat the content below as the canonical workflow.\n\n"
        f"{text}"
    )


def cleanup(target_dir: Path, manifest: Path, sibling_manifest: Path) -> int:
    """Remove previously installed overlay skills, per the overlay manifest.

    Never removes a folder the sibling (memory core) manifest also claims. Both installers write
    into one skills directory, so a stale entry — a procedure that moved core<->overlay in an
    earlier session — must not delete a skill the other installer owns. This is what makes the
    two installers order-independent.
    """
    if not manifest.exists():
        return 0
    sibling: set[str] = set()
    if sibling_manifest.exists():
        raw = sibling_manifest.read_text(encoding="utf-8").splitlines()
        sibling = {ln.strip() for ln in raw if ln.strip()}
    removed = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        folder = line.strip()
        if not folder or folder in sibling:
            continue
        path = target_dir / folder
        if path.is_dir():
            shutil.rmtree(path)
            removed += 1
    return removed


def install(
    target_dir: Path | str,
    manifest_name: str,
    sibling_manifest_name: str,
    root: Path | str = _ROOT,
    output_dir: Path | str | None = None,
) -> tuple[list[str], int]:
    """Compile the overlay and install it as skills into ``target_dir``.

    Returns ``(installed_skill_names, removed_count)``.
    """
    root = Path(root)
    target_dir = Path(target_dir)
    output_dir = Path(output_dir) if output_dir else root / "output"
    target_dir.mkdir(parents=True, exist_ok=True)

    reports = _cc.compile_all(root, output_dir, verbose=False)

    removed = cleanup(
        target_dir, target_dir / manifest_name, target_dir / sibling_manifest_name
    )

    installed: list[str] = []
    manifest_lines: list[str] = []
    for report in reports:
        text = Path(report.out_path).read_text(encoding="utf-8")
        folder = target_dir / f"{FOLDER_PREFIX}{report.name}"
        folder.mkdir(parents=True, exist_ok=True)
        # Encode before opening the target: a write that fails mid-encode would otherwise
        # truncate a file that was fine a moment ago.
        data = build_skill(report.name, text).encode("utf-8")
        tmp = folder / "SKILL.md.tmp"
        tmp.write_bytes(data)
        tmp.replace(folder / "SKILL.md")
        installed.append(report.name)
        manifest_lines.append(folder.name)

    (target_dir / manifest_name).write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8", newline="\n"
    )
    return installed, removed


def register_path(instructions_file: Path, overlay_root: Path = _ROOT) -> str:
    """Define ``[path-to-agent-memory-fleet]`` in a platform's global instructions file.

    The overlay's procedures reach their scripts and templates through that placeholder, and only
    this installer knows where the standalone repo was cloned — so it registers the definition
    itself, UUID-guarded so re-runs cannot duplicate the line. Without it, every
    ``fleet-scripts/*.sh`` call and template copy in an installed skill is a dangling reference.

    The path is written with forward slashes: accepted by Windows tooling *and* by the bash that
    runs the overlay's shell scripts, where a backslash path would be read as escape sequences.
    """
    if not instructions_file.is_file():
        return (
            f"  NOTE: {instructions_file} not found — could not register\n"
            "        [path-to-agent-memory-fleet]. Run the memory-core setup for this\n"
            "        platform first (it creates the file), then re-run this installer."
        )
    if _PATH_DEF_UUID in instructions_file.read_text(encoding="utf-8"):
        return "  [path-to-agent-memory-fleet] already registered — skipped."

    path_value = Path(overlay_root).as_posix()
    line = (
        f"\n- **[path-to-agent-memory-fleet]** = `{path_value}`"
        f"  <!-- overlay-path-def {_PATH_DEF_UUID} -->\n"
    )
    with instructions_file.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
    return f"  Registered [path-to-agent-memory-fleet] = {path_value}"


def register_env(instructions_file: Path) -> str:
    """Ensure the environment declarations Hermod relies on are present.

    ``[CORE-ACCESS]`` and ``[CORE-MCP-URL]`` are the overlay's: they decide markdown-vs-mcp for
    the overlay's own handoffs, and the OS + bash notes are what its shell scripts assume. The
    core's compiled memory supplies them when it is installed, so this writes them **only when
    they are absent** — the guard is the declaration itself, never the overlay's UUID, so a
    core-provided block is never duplicated. Values come from the same env vars the core's
    ``write-to-*`` scripts use (``CORE_ACCESS`` / ``CORE_MCP_URL``).
    """
    if not instructions_file.is_file():
        return (
            f"  NOTE: {instructions_file} not found — could not register the environment\n"
            "        declarations. Run the memory-core setup for this platform first (it creates\n"
            "        the file), then re-run this installer."
        )
    if "**[CORE-ACCESS]**" in instructions_file.read_text(encoding="utf-8"):
        return "  [CORE-ACCESS] / [CORE-MCP-URL] already present — skipped."

    mode = os.environ.get("CORE_ACCESS", "markdown")
    url = os.environ.get("CORE_MCP_URL", "<unset>")
    os_name = _OS_NAMES.get(sys.platform, sys.platform or "Unknown")
    block = (
        "\n"
        f"- **Operating System**: {os_name}\n"
        "- **Claude Code Bash Tool**: Runs in **Git Bash** (NOT CMD or PowerShell)\n"
        "  - Use Unix-style commands: `cp`, `rm`, `ls`, `mkdir`, `cat`, `grep`\n"
        "  - Use forward slashes: `/c/Users/username/.claude/` "
        "(not `C:\\Users\\username\\.claude\\`)\n"
        '  - Use Unix conditionals: `test -f file && echo "exists"` (not `if exist file`)\n'
        "  - CMD syntax like `if exist ... (echo) else (echo)` will FAIL\n"
        f"- **[CORE-ACCESS]** = `{mode}` (which form of the memory core this machine uses: "
        "`markdown` for the installed commands, `mcp` for the procedures served over a connected "
        "server)\n"
        f"- **[CORE-MCP-URL]** = `{url}` (the endpoint the served core is reached at; only the "
        "layer that opens the connection acts on this, never the agent)"
        f"  <!-- overlay-env-def {_ENV_DEF_UUID} -->\n"
    )
    with instructions_file.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    return f"  Registered [CORE-ACCESS] = {mode} ([CORE-MCP-URL] = {url}) + OS/bash notes"


def register_layer_access(instructions_file: Path, layer: str, uuid: str) -> str:
    """Define ``[<LAYER>-ACCESS]`` / ``[<LAYER>-MCP-URL]`` in a platform's global instructions file.

    The declaration names how one repo's *layer* is reached: ``markdown`` for installed
    commands/skills, ``mcp`` for procedures served over a connected server. A caller reads the
    target layer's declaration, so each layer's own installer writes it. UUID-guarded so re-runs
    cannot duplicate the line.
    """
    if not instructions_file.is_file():
        return (
            f"  NOTE: {instructions_file} not found - could not register\n"
            f"        [{layer}-ACCESS]. Run the memory-core setup for this platform first,\n"
            "        then re-run this installer."
        )
    marker = f"**[{layer}-ACCESS]**"
    if marker in instructions_file.read_text(encoding="utf-8"):
        return f"  [{layer}-ACCESS] already registered - skipped."

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
    with instructions_file.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(block)
    return f"  Registered [{layer}-ACCESS] = {mode} ([{layer}-MCP-URL] = {url})"


def run(
    platform: str,
    target_dir: Path,
    manifest_name: str,
    sibling_manifest_name: str,
    instructions_file: Path,
) -> int:
    """Shared ``main()`` body for a platform entry point."""
    print(f"=== Setup agent-memory-fleet OVERLAY {platform} Skills ===\n")
    print(f"Source (overlay): {_ROOT / 'output'}")
    print(f"Target:           {target_dir}\n")

    if not (_ROOT / "procedures").is_dir():
        print(f"Error: overlay procedures directory not found: {_ROOT / 'procedures'}")
        return 1

    installed, removed = install(target_dir, manifest_name, sibling_manifest_name)

    if removed:
        print(f"Cleaned up {removed} stale overlay skills\n")
    if not installed:
        print("Error: no procedures compiled — nothing installed.")
        return 1

    print(f"Successfully installed {len(installed)} fleet procedures!\n")
    print(register_path(instructions_file))
    print(register_env(instructions_file))
    print(register_layer_access(instructions_file, "FLEET", _FLEET_ACCESS_UUID))
    print("\nInstalled overlay skills:")
    for name in installed:
        print(f"  {FOLDER_PREFIX}{name}")
    print(
        "\nSkills are model-invoked: ask for the procedure in your own words "
        "(for example \"use the quick-wizard skill\") rather than typing a slash command."
    )
    return 0
