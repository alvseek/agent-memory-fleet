# Load Fleet

Load the project's fleet roster (who's who) and surface the fleet commands. Read-only: it tells you which teammates you can consult or hand off to, and which commands do that. Reach for it when a task needs another agent's expertise and you are not already holding the roster.

## Arguments

`$ARGUMENTS`

- `/load-fleet [project-name]` → Load the roster for the given project
- `/load-fleet` → Auto-detect the project from the git repo (or cwd)

If no arguments provided, auto-detect from `git rev-parse --show-toplevel` (basename) or the cwd.

---

## Layer access

A handoff to another layer resolves through that layer's access declaration, which the caller reads. An **absent** declaration means `markdown`.

- `[CORE-ACCESS]` / `[CORE-MCP-URL]`: how the memory core (`munnin`) is reached. `/ask-agent` uses it to awaken a teammate.
- `[CODING-ACCESS]` / `[CODING-MCP-URL]`: how the coding overlay (`hermod-coding`) is reached. `/ask-agent` uses it to give a spawned teammate the coding awakening.
- `[FLEET-ACCESS]` / `[FLEET-MCP-URL]`: how this fleet (`hermod-fleet`) is reached.

## Procedure

### Step 1: Resolve Project Name

Auto-detect from `git rev-parse --show-toplevel` (basename) or use the provided argument.

### Step 2: Read the Roster

Read `[AGENT-MEMORY-PATH]/shared-memory/[project-name]/fleet-agents.md` (silent skip if missing).

If it does not exist, report *"No fleet for this project yet - use `/setup-fleet` to define one."* and stop.

### Step 3: Report

Report the roster and the fleet commands:

- **Roster**: each teammate on the project's fleet (domain, specialty, when to consult).
- **Commands**:
  - `/ask-agent [Name|UUID]` - blocking consultation with a teammate
  - `/delegate-agent [Name|UUID]` - background handoff of a task
  - `/setup-fleet` - define the team (once per project)

The active-session map (`fleet-map.csv`) is created automatically by the fleet scripts when agents first communicate.

---
