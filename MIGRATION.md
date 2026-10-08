# Migration Note - extracted from the coding overlay (2026-10-08)

The fleet procedures, scripts, and templates were **moved out of** the coding overlay
(`agent-memory-coding-skill` / Hermod-coding) into this standalone repo, splitting the
overlay into the **Hermod family**: `hermod-coding` + `hermod-fleet`.

## What moved

- **procedures**: `setup-fleet`, `ask-agent`, `delegate-agent`
- **fleet-scripts**: `ask-agent.sh`, `delegate-agent.sh`, `wrap-up-agent.sh`, `fleet-common.sh`
- **templates**: `fleet-agents-template.md`, `fleet-map-template.csv`

## New here

- **`load-fleet`**: reads the project's fleet roster and surfaces the fleet commands. It
  replaces the roster read and report that used to live inside the overlay's `awaken-coder`.

## What did not move

- The fleet **data** (`shared-memory/[project]/fleet-agents.md`, `fleet-map.csv`) stays in the
  central `@agent-memory` store. Only the operations moved.

## History

Per-file commit history remains in `agent-memory-coding-skill`. This repo starts with a
**fresh initial commit**, mirroring how the coding overlay itself was extracted from the
memory core (its own `MIGRATION.md`).

## Access declarations

A cross-layer handoff resolves through the target layer's access declaration, which the caller
reads: `[CORE-ACCESS]`, `[CODING-ACCESS]`, `[FLEET-ACCESS]`. This repo owns `[FLEET-ACCESS]`.
See the ADR in `docs/adr/` for the model.
