# ADR-001: The fleet transport contract

**Date**: 2026-10-21

**Status**: Accepted

---

## Problem

The fleet spawned agents with `claude --print --session-id <uuid>`, and that UUID was simultaneously the fleet's identity for the session and the Claude session id. OpenCode forces `ses_` prefixed ids, takes a different model vocabulary, and needs a different non-interactive switch. Background delegation depended on one harness's shell facility (`run_in_background` plus a task notification), which no other platform shares. A fleet that must run on more than one harness needs a contract that names which facts belong to the fleet and which belong to the platform.

---

## Decision

**We decided to**: separate the fleet's session identity from the platform's session reference, and put every platform-specific fact behind one adapter boundary.

A fleet session is identified by its machine and its platform reference, stored together. Each platform contributes exactly four facts: how a session is created, how it is resumed, how a model is named, and how a non-interactive turn is approved. Execution is always a child process on the user's machine, because the session state lives there. Detachment belongs to the runtime, not to the harness: a delegated turn is the same blocking call started detached, with its output captured to a file.

**Why we chose this:**
- A platform's session id is not portable, and the two platforms disagree on its shape. Storing it as the fleet identity makes the other platform unrepresentable.
- A single `claude`-shaped shim hides the difference in flags rather than modelling it, and fails at the first argument that does not translate.
- Harness background facilities are the least portable part of any agent platform; owning detachment removes the only piece that could never generalize.

---

## What to Build (Requirements)

**Core Requirements:**
- A session ref that accepts a valid UUID (Claude Code) or a `ses_` value (OpenCode), routed by its own shape.
- Detection of the calling platform from the environment, with an explicit override for a harness that sets no marker.
- Two adapters: Claude Code (`--print --session-id` / `--resume`) and OpenCode (`run --session --auto`), each with its own model resolution.
- A machine identity that is stable and generated, never a hostname.
- No permission bypass forced by the fleet; a platform's non-interactive approval switch is used, but nothing broader.
- A dry-run mode that prints the argv, so the branch is testable without spawning an agent.

**Success Criteria:**
- A blocking consult answers on both platforms.
- A resume routes to the platform that owns the ref, whatever platform the caller is on.
- The argv for new, resume, and per-platform model resolution is asserted by tests.
- A background delegation completes through the runtime's own detachment, with the reply readable afterwards.

---

## Alternatives Rejected

- **A `claude` shim that calls OpenCode**: it must translate every flag, so it is the adapter with a misleading name.
- **Keep the platform session id as the fleet identity**: makes a second platform unrepresentable and a resume from the other platform impossible to describe.
- **A hosted service that spawns agents**: tools execute on the server, so the agent would run on the wrong machine.
- **Depend on the harness's background facility**: it is the one mechanism no two harnesses share.

---

**Full context**: [High Wizard plan](../../plans/2026-10-20-agent-memory-fleet-fleet-delivery.md)
