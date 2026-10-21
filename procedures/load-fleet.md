# Load Fleet

Load the project's fleet roster (who's who) and surface the fleet commands. Read-only: it tells you which teammates you can consult or hand off to, and which commands do that. Reach for it when a task needs another agent's expertise and you are not already holding the roster.

## Arguments

`$ARGUMENTS`

- `/load-fleet [project-name]` → Load the roster for the given project
- `/load-fleet` → Auto-detect the project from the git repo (or cwd)

If no arguments provided, auto-detect from `git rev-parse --show-toplevel` (basename) or the cwd.

---

## Layer access

A handoff to another layer resolves through that layer's access declaration, which the caller reads.

- `[CORE-ACCESS]` / `[CORE-MCP-URL]`: how the memory core (`munnin`) is reached. A consult uses it to awaken a teammate.
- `[PROJECT-ACCESS]` / `[PROJECT-MCP-URL]`: how the coding overlay (`hermod`) is reached. A consult uses it to give a spawned teammate the coding awakening.
- `[FLEET-ACCESS]` / `[FLEET-MCP-URL]`: how this fleet (`einherjar`) is reached.

## Procedure

### Step 1: Resolve Project Name

Auto-detect from `git rev-parse --show-toplevel` (basename) or use the provided argument.

### Step 2: Read the Roster

Call `list_shared_context(project="<project>")` and find the row whose `theme` is `fleet-agents`.

- **Absent**: report *"No fleet for this project yet. Use `/setup-fleet` to define one."* and stop.
- **Present**: read its body with `get(uuid)`. That body is the roster table.

There is no file to fall back to. The roster has one home, the project's context, and an absent row means the project has no fleet.

### Step 3: Report

Report the roster and the fleet commands:

- **Roster**: each teammate on the project's fleet (domain, specialty, when to consult, and the model when one is named).
- **Commands**:
  - `/ask-agent [Name|SessionRef]` - blocking consultation with a teammate
  - `/delegate-agent [Name|SessionRef]` - background handoff of a task
  - `/setup-fleet` - define the team (once per project)

This procedure reads the roster only. Active sessions are the fleet registry's business: they are written when a consult starts, and they are not part of this roster.

---
