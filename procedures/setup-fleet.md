# Setup Fleet

Create the project's fleet roster: who is on the team, what each is expert in, when to consult them, and which model each runs. The roster is **one memory record** in the project's context, not a file. Run this once per project, and run it again to change the team.

## Arguments

`$ARGUMENTS`

- `/setup-fleet [project-name]` → Create or update the roster for the given project
- `/setup-fleet` → Auto-detect the project from the git repo, or ask

If no arguments provided, try to auto-detect from `git rev-parse --show-toplevel` (basename). If that fails, ask: "What is the project name?"

---

## Procedure

### Step 1: Resolve Project Name

Auto-detect from `git rev-parse --show-toplevel` (basename) or use the provided argument. The project name is the key the roster is filed under, so it must be the repository's identity, not a folder nickname.

### Step 2: Read the Knowledge Template Stamp

Call `read_resource("knowledge-file-template")` and take the value on its `template_version:` line. A `knowledge` record is refused without the stamp matching the template it was built against, so read it now instead of guessing or reusing an old value.

### Step 3: Find an Existing Roster

Call `list_shared_context(project="<project>")` and look for the row whose `theme` is `fleet-agents`.

- **Found**: this is an update. Keep its `uuid`, and read the current body with `get(uuid)` before rewriting it.
- **Not found**: this is a create.

### Step 4: Define the Team

Present the roster's shape and ask [USER-NAME] to fill it:

"I've opened the roster for **[project-name]**. For each agent that will work on this project, I need:
- **Agent Domain**: the agent name (e.g., Backend Django, Frontend Nextjs, Software Architect)
- **Specialty**: what they are expert in
- **When to Consult**: when another agent should ask them for help
- **Model**: optional; leave blank for the platform default

Which agents will be on this project's fleet?"

Fill a table in this shape:

```
| Agent Domain | Specialty | When to Consult | Model |
|---|---|---|---|
| Backend Django | Django models, APIs, data modeling | Backend implementation, API design | |
```

The Model column is optional. On Claude Code it holds an alias (`haiku`, `sonnet`, `opus`); on OpenCode it holds `provider/model`. A blank value means the platform's default model.

### Step 5: Write the Roster

**Create** when no row was found. One call, no file:

```
insert(
  scope="shared",
  record_type="knowledge",
  project="<project>",
  title="fleet-agents",
  content="<the completed table>",
  content_summary="The project's fleet roster: who is on the team, and when to consult them.",
  template_version="<the stamp from Step 2>",
  tags=["fleet", "roster"]
)
```

`scope="shared"` is the project's cross-agent layer: a roster belongs to the team, not to one agent. The body is the table alone; the title and the summary are what a listing shows, so the body does not repeat them as a heading.

**Update** when a row was found. Replace the body in place:

1. `get(uuid)` and keep the exact body you read.
2. `edit(uuid, old_string="<the old body>", new_string="<the new table>")`. The old string must match byte for byte, so paste the body you just read rather than retyping it.
3. If the old summary no longer describes the roster, call `edit_metadata(uuid, content_summary="...")`.

Do not delete and re-insert. That changes the uuid, and a roster's identity should survive an edit.

### Step 6: Confirm

Report:

```
Fleet saved for [project]:
  - Record: fleet-agents (uuid [uuid])
  - Agents defined: [count]
  - Nothing written to disk: the roster lives in the project's context.
```

If this was an update, say so, and mention the previous agent count if it changed.

---

**Related**: `/load-fleet` reads this record; `/ask-agent` and `/delegate-agent` consult the agents it names.
