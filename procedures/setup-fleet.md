# Setup Fleet

Initialize the fleet agents directory for a project. Creates `fleet-agents.md` (who's who) in the project's shared memory folder. Run once per project initiation. The `fleet-map.csv` (active sessions) is auto-created by the fleet scripts when agents first communicate.

## Arguments

`$ARGUMENTS`

- `/setup-fleet [project-name]` → Initialize fleet for the given project
- `/setup-fleet` → Will auto-detect project name from git repo or ask

If no arguments provided, try to auto-detect from git repo name. If that fails, ask: "What is the project name?"

---

## Procedure

### Step 1: Resolve Project Name

Auto-detect from `git rev-parse --show-toplevel` (basename) or use the provided argument.

### Step 2: Create Project Shared Memory Directory

Create the directory if it doesn't exist:
`[AGENT-MEMORY-PATH]/shared-memory/[project-name]/`

### Step 3: Create Fleet Agents File

Copy the template and replace the project name:
- Source: `[path-to-agent-memory-fleet]/templates/fleet-agents-template.md`
- Target: `[AGENT-MEMORY-PATH]/shared-memory/[project-name]/fleet-agents.md`

Replace `{PROJECT-NAME}` with the actual project name.

### Step 4: Fill Fleet Agents

Present the fleet-agents.md to [USER-NAME] and ask them to define the team:

"I've created the fleet directory for **[project-name]**. Let's define the team.

For each agent that will work on this project, I need:
- **Agent Domain**: The agent name (e.g., Backend Django, Frontend Nextjs, Software Architect)
- **Specialty**: What they're expert in
- **When to Consult**: When other agents should ask this one for help

Which agents will be on this project's fleet?"

Fill the table based on [USER-NAME]'s input. Remove the example rows.

### Step 5: Confirm

Show the completed fleet-agents.md to [USER-NAME] for confirmation.

Report:
```
Fleet initialized for [project-name]:
  - Fleet agents: [AGENT-MEMORY-PATH]/shared-memory/[project-name]/fleet-agents.md
  - Agents defined: [count]
  - Fleet map: Will be auto-created when agents first communicate
```

---
