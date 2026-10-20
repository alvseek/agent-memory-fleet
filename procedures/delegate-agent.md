# Delegate Agent

Send a background delegation request to another specialized agent. The target agent awakens (if new) or resumes (if given a session ref) and works autonomously on the task while the caller continues working. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

## Arguments

`$ARGUMENTS`

- `/delegate-agent [Name|SessionRef]` → Construct structured prompt, then delegate to the target agent
- `/delegate-agent` → Will ask which agent to delegate to

If no arguments provided, ask: "Which agent do you want to delegate to? Provide a Name (to awaken) or a session ref (to resume)."

---

## Procedure

### Step 1: Resolve Target

Parse the argument:
- If it is a session ref, this is a **resume**. A UUID is a Claude Code session; a `ses_...` value is an OpenCode session, and the ref's shape decides the platform.
- If it's a name (e.g., "Backend Django", "Frontend Nextjs"), this is a **new awakening** — the script verifies the agent exists (a store folder, or a row in the project's roster) and starts a new session on the platform detected from your environment. `FLEET_PLATFORM=claude|opencode` overrides that detection.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model haiku"` → TARGET=`3f8a2b1c-...`, MODEL=`haiku`
- `"ses_eac06c991ffd..."` → TARGET=`ses_eac06c991ffd...`, MODEL=`""`

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

Run `ask-agent.sh` with your harness's **background** mode:

- **Claude Code**: the Bash tool with **`run_in_background: true`**.
- **OpenCode**: the shell tool with **`background: true`**.
- Anywhere else: the same script started detached, with stdout redirected to a file.

```bash
bash "[path-to-agent-memory-fleet]/fleet-scripts/ask-agent.sh" "[Name|SessionRef]" "[structured prompt]" "[theme]" "" "[model]"
```

Pass empty string for the 4th arg (fleet-map — script auto-resolves it). Pass model as 5th arg; use empty string if no model was specified.

Your harness returns a **task or handle** immediately. Note it — the agent is now working in the background, and the script's first stdout line is the session ref.

### Step 4: Continue Working

Do not block. Continue your own work.

**When the harness reports the background command finished**:
- Read the output file or result your harness gives you
- **Name mode** (new awakening): first line of output = session ref — save it for future `/ask-agent [SessionRef]` or `/delegate-agent [SessionRef]` calls. Remaining lines = agent's full response.
- **Ref mode** (resume): output contains the agent's full response only.

To wrap up a completed session: `bash "[path-to-agent-memory-fleet]/fleet-scripts/wrap-up-agent.sh" [SessionRef]`

---
