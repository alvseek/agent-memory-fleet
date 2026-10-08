# Delegate Agent

Send a background delegation request to another specialized agent. The target agent awakens (if new) or resumes (if UUID) and works autonomously on the task while the caller continues working. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

## Arguments

`$ARGUMENTS`

- `/delegate-agent [Name|UUID]` → Construct structured prompt, then delegate to the target agent
- `/delegate-agent` → Will ask which agent to delegate to

If no arguments provided, ask: "Which agent do you want to delegate to? Provide a Name (to awaken) or UUID (to resume)."

---

## Procedure

### Step 1: Resolve Target

Parse the argument:
- If it looks like a UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`), this is a **resume**
- If it's a name (e.g., "Backend Django", "Frontend Nextjs"), this is a **new awakening** — verify the agent folder exists at `[AGENT-MEMORY-PATH]/agent-[folder-name]/`

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/UUID portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model haiku"` → TARGET=`3f8a2b1c-...`, MODEL=`haiku`
- `"Backend Django"` → TARGET=`Backend Django`, MODEL=`""`

### Step 2: Construct Structured Prompt

Fill this template based on the current task context. All fields are required:

```
## Theme
[Short label for the fleet map — e.g., "user auth middleware", "inventory tags UI"]

## Context
[What you're working on and why this task needs to be delegated]

## Task
[Clear description of what the target agent should accomplish]

## Acceptance Criteria
[How do we know the task is done? What conditions must be met?]

## Expected Deliverables
[What files, code, documents, or outputs should be produced?]

## Constraints
[Any limitations, patterns to follow, things to avoid, or dependencies to be aware of]
```

Do NOT send vague or open-ended prompts. Be specific about the task, what "done" looks like, and what constraints apply.

### Step 3: Execute

Run `ask-agent.sh` using the Bash tool with **`run_in_background: true`**:

```bash
bash "[path-to-agent-memory-fleet]/fleet-scripts/ask-agent.sh" "[Name|UUID]" "[structured prompt]" "[theme]" "" "[model]"
```

Pass empty string for the 4th arg (fleet-map — script auto-resolves it). Pass model as 5th arg; use empty string if no model was specified.

The Bash tool returns a **task ID** immediately. Note it — the agent is now working in the background.

### Step 4: Continue Working

Do not block. Continue your own work.

**When `<task-notification>` arrives** — the delegated agent has finished:
- Read the output file path from the notification
- **Name mode** (new awakening): first line of output file = UUID — save it for future `/ask-agent [UUID]` or `/delegate-agent [UUID]` calls. Remaining lines = agent's full response.
- **UUID mode** (resume): output file contains the agent's full response only.

To wrap up a completed session: `bash "[path-to-agent-memory-fleet]/fleet-scripts/wrap-up-agent.sh" [UUID]`

---
