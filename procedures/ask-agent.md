# Ask Agent

Send a blocking consultation request to another specialized agent. The target agent awakens (if new) or resumes (if given a session ref), processes the structured prompt, and returns a response. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

## Arguments

`$ARGUMENTS`

- `/ask-agent [Name|SessionRef]` → Construct structured prompt, then send to the target agent
- `/ask-agent` → Will ask which agent to consult

If no arguments provided, ask: "Which agent do you want to consult? Provide a Name (to awaken) or a session ref (to resume)."

---

## Procedure

### Step 1: Resolve Target

Parse the argument:
- If it is a session ref, this is a **resume**. A UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) is a Claude Code session; a `ses_...` value is an OpenCode session. The ref's own shape decides which platform the turn goes to.
- If it's a name (e.g., "Backend Django", "Software Architect"), this is a **new awakening** — the script verifies the agent exists (a store folder, or a row in the project's roster) and starts a new session on the platform detected from your environment. OpenCode sets `OPENCODE=1`; Claude Code sets `CLAUDECODE=1`. `FLEET_PLATFORM=claude|opencode` overrides the detection.

The ref and the platform are separate facts, because the two platforms name sessions differently. Never pass a `ses_...` value where a UUID is expected, or the reverse.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/UUID portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model sonnet"` → TARGET=`3f8a2b1c-...`, MODEL=`sonnet`
- `"Backend Django"` → TARGET=`Backend Django`, MODEL=`""`

### Step 2: Construct Structured Prompt

Fill this template based on the current task context. All fields are required:

```
## Theme
[Short label for the fleet map — e.g., "user auth patterns", "DB schema review"]

## Context
[What you're working on and why you need this agent's expertise]

## Request
[Specific question or task — what exactly you need from the target agent]

## Expected Output
[What format/detail the response should be in]
```

Do NOT send vague or open-ended prompts. Be specific about what you need and what the response should look like.

### Step 3: Execute

Run the script (blocking):

```bash
bash "[path-to-agent-memory-fleet]/fleet-scripts/ask-agent.sh" "[Name|SessionRef]" "[structured prompt]" "[theme]" "" "[model]"
```

Pass empty string for the 4th arg (fleet-map — script auto-resolves it). Pass model as 5th arg; use empty string if no model was specified.

Wait for the response. This blocks until the target agent responds.

### Step 4: Process Response

Use the target agent's response to continue your work. Note the session ref from the script output (a UUID on Claude Code, `ses_...` on OpenCode) so you can resume this session later if needed.

---
