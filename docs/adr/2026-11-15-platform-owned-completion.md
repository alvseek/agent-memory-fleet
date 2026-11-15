# ADR-004: The invoking platform owns completion delivery

**Date**: 2026-11-15

**Status**: Accepted

---

## Problem

Einherjar's detached `delegate` and `spawn --background` commands return a reference and write result files, but do not notify the invoking agent when the worker finishes. A supervisor can therefore lose a completed or failed worker unless it polls. An implementation-plan handoff requires completion to reach the invoking session so that the supervisor can verify progress, continue the worker, or surface a human decision.

---

## Decision

**We decided to**: remove client-owned detached execution and use the invoking platform's completion-aware task facility around a blocking Einherjar command.

The CLI retains blocking `ask` and `spawn`, which record and run one local worker turn and return its result. `/delegate-agent` and `/dispatch-plan` run that command through the invoking platform's background shell tool only when that tool reports completion to the invoking session. Without such a tool, the command remains blocking. There is no detached or polling fallback and no new notification service.

This supersedes only the client-detachment decision, rationale and associated success criterion in [ADR-001](2026-10-21-fleet-transport-contract.md). Its session-reference model, machine identity, adapter boundary and local execution remain in force. The old decision remains a historical record.

**Why we chose this:**
- Completion delivery is part of supervision, not a property of a readable result file.
- OpenCode already provides a completion notification for its background shell tasks; a harmless command demonstrated delivery to the invoking session. Claude Code documents background shell tasks, but that path still needs runtime verification.
- Blocking fallback preserves result delivery without requiring every platform to implement the same background facility.

---

## What to Build (Requirements)

Keep execution and notification ownership explicit: Einherjar runs a turn, the platform delivers the task result, and the invoking agent judges the plan's progress.

**Core Requirements:**
- Remove CLI `delegate`, `spawn --background`, private `_turn` and their detached-process implementation.
- Preserve blocking new/resumed sessions, explicit model selection, anonymous spawn, registry tracking, credentials and readable historical results.
- Update active procedures, help and documentation together; explain migration for callers of the removed commands.
- Add `/dispatch-plan` with a fully read plan/rules handoff, a startup announcement, same-session continuation and explicit human escalation boundaries.
- Use platform task completion, not periodic reads of output or registry state, to know when the supervised command ended.
- If a platform task is interrupted or times out, treat the worker's state as unresolved until checked; never start a duplicate turn merely because a result did not arrive.

**Success Criteria:**
- Removed entrypoints refuse execution without launching a worker.
- Named and anonymous blocking calls and resumes retain their existing execution and registry contracts.
- On a runtime-verified platform, a worker result reaches the invoking session through its task-completion mechanism, and the supervisor continues the same worker without polling or duplicate launches.

---

## Alternatives Rejected

- **Keep client-owned detachment and read results later**: readable output does not deliver completion to a supervisor.
- **Add per-platform callbacks or a notification service**: adds lifecycle and delivery machinery when the invoking platforms already own completion-aware tasks.
- **Blocking execution only everywhere**: retained as the fallback, but needlessly prevents parallel work on platforms with completion-aware task tools.

---

**Full context**: [Dispatch-plan High Wizard draft](https://github.com/alvseek/einherjar-deploy/blob/main/plans/2026-11-14-einherjar-dispatch-plan.md). This is the planning record in the deployment repository, not a runtime dependency.

---

**ADR Template for Architecture Decision Records**

*This document serves as a SPECIFICATION that tells implementation agents WHAT to build. The implementation protocol (High Wizard/Quick Wizard) will figure out HOW to build it.*
