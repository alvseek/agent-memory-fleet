# Ask Agent

Send a blocking consultation request to another specialized agent. The target agent awakens (if new) or resumes (if UUID), processes the structured prompt, and returns a response. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

## Arguments

`$ARGUMENTS`

- `/ask-agent [Name|UUID]` → Construct structured prompt, then send to the target agent
- `/ask-agent` → Will ask which agent to consult

If no arguments provided, ask: "Which agent do you want to consult? Provide a Name (to awaken) or UUID (to resume)."

---

## Procedure

### Step 1: Resolve Target

Parse the argument:
- If it looks like a UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`), this is a **resume**
- If it's a name (e.g., "Backend Django", "Software Architect"), this is a **new awakening** — verify the agent folder exists at `[AGENT-MEMORY-PATH]/agent-[folder-name]/`

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
bash "[path-to-agent-memory-fleet]/fleet-scripts/ask-agent.sh" "[Name|UUID]" "[structured prompt]" "[theme]" "" "[model]"
```

Pass empty string for the 4th arg (fleet-map — script auto-resolves it). Pass model as 5th arg; use empty string if no model was specified.

Wait for the response. This blocks until the target agent responds.

### Step 4: Process Response

Use the target agent's response to continue your work. Note the UUID from the script output so you can resume this session later if needed.

---
