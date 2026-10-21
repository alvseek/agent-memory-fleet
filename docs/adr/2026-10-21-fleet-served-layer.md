# ADR-003: The fleet layer is served, not installed

**Date**: 2026-10-21

**Status**: Accepted

---

## Problem

Every layer of the family has been delivered twice: as installed markdown (skills on OpenCode and Codex, commands on Claude Code) and as procedures served over MCP. The fleet was installed, so its procedures lived in a skills directory per harness, its templates were copied from a local clone, and `[FLEET-ACCESS]` recorded which of the two forms a machine used. The family is now retiring the installed form: `agent-memory-doc` and `heimdall-map` move to served layers as well. A fleet that keeps an installed path would be the one layer still writing markdown into a harness that no longer expects it.

There is a second constraint. On OpenCode, an MCP prompt is exposed as a command a person types, so a procedure served only as a prompt cannot be invoked by an agent mid-task. The fleet's whole purpose is agent-to-agent work, so delivery has to reach the agent, not only the user.

---

## Decision

**We decided to**: serve the fleet layer from Einherjar and remove the installed form entirely, with every procedure reachable both as a prompt and through a `read_procedure` tool.

`einherjar-server` vendors `agent-memory-fleet` as a content submodule and composes its procedures per request. The four procedures are prompts for a person and tool results for an agent; the two templates are resources, so no served text points at a local clone. `einherjar install` performs the local setup the markdown installers used to do: it registers the MCP server and removes the skills the previous manifest installed. `[FLEET-ACCESS]` becomes `mcp` with `[FLEET-MCP-URL] = https://einherjar.lok.quest/mcp`, and the markdown branch in the procedures is deleted rather than kept behind a flag.

**Why we chose this:**
- The family direction is served layers; a markdown fallback in the fleet would be debt against a decision already made.
- A prompt-only face cannot be invoked by an agent on OpenCode, which is the platform the council now runs on.
- Serving both ways costs one tool and preserves the user's command path, so nothing is lost by dropping the installed form.

---

## What to Build (Requirements)

**Core Requirements:**
- The service composes the four procedures from the pinned content submodule, serving them as prompts and through `read_procedure(name)`.
- Both templates are served as resources with stable names.
- A test proves the served text equals the repo's compiled procedure byte for byte.
- `einherjar install --harness` registers the MCP server, writes the access declaration, and removes the skills named by the old fleet manifest.
- The fleet repo's markdown installers are retired; the compiler remains as CI validation.
- No procedure names a shell script or a local path.

**Success Criteria:**
- A harness with no fleet clone can read every procedure and template.
- An agent on OpenCode fetches a procedure through the tool and completes a consult.
- A machine that had fleet skills installed ends with none, and one MCP entry.
- `[FLEET-ACCESS]` is `mcp` and the URL resolves.

---

## Alternatives Rejected

- **Prompts only**: the agent cannot invoke a procedure on OpenCode, which makes the fleet user-driven.
- **Keep installed skills beside the served face**: contradicts the family's retirement of markdown and keeps two sources of procedure truth.
- **One installed pointer skill that fetches the procedure**: still an installed markdown file, and it needs updating per harness.
- **A tool that executes the procedure server-side**: a tool runs on the server, so the spawn would happen on the wrong machine.

---

**Full context**: [High Wizard plan](../../plans/2026-10-20-agent-memory-fleet-fleet-delivery.md)
