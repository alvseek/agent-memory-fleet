# Ask Agent

Send a blocking consultation request to another specialized agent. The fleet client records the consult, awakens the target through the served coding overlay, sends the structured prompt, and returns the reply. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

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
- If it's a name (e.g., "Backend Django", "Software Architect"), this is a **new awakening**. The client starts a new session on the platform detected from your environment: OpenCode sets `OPENCODE=1`; Claude Code sets `CLAUDECODE=1`. `EINHERJAR_PLATFORM=claude|opencode` overrides the detection.

The client does not check a roster: use a domain the project's fleet names. The memory server is the authority on whether an agent exists, and a wrong domain fails at awakening.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model sonnet"` → TARGET=`3f8a2b1c-...`, MODEL=`sonnet`
- `"Backend Django"` → TARGET=`Backend Django`, MODEL=`""`

### Step 2: Construct Structured Prompt

Fill this template based on the current task context. All fields are required:

```
## Theme
[Short label for the fleet registry — e.g., "user auth patterns", "DB schema review"]

## Context
[What you're working on and why you need this agent's expertise]

## Request
[Specific question or task — what exactly you need from the target agent]

## Expected Output
[What format/detail the response should be in]
```

Do NOT send vague or open-ended prompts. Be specific about what you need and what the response should look like.

### Step 3: Execute

Run the fleet client (blocking):

```bash
einherjar ask "[Name|SessionRef]" --prompt "[structured prompt]" --theme "[theme]" [--model <value>]
```

The client writes the session row, spawns the turn, and closes the row when it ends. The command's first stdout line is the session ref; the reply follows it.

Check the client is present before a consult: if `einherjar` is not on `PATH`, report that and the install command (`uv tool install einherjar`) rather than proceeding.

### Step 4: Process Response

Use the target agent's response to continue your work. Keep the session ref from the first line (a UUID on Claude Code, `ses_...` on OpenCode) so you can resume this session later with `/ask-agent [SessionRef]`.

---
