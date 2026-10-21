# Delegate Agent

Send a background delegation request to another specialized agent. The fleet client records the consult, awakens the target through the served coding overlay, starts the turn detached, and returns immediately. The caller continues its own work while the target works. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

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
- If it's a name (e.g., "Backend Django", "Frontend Nextjs"), this is a **new awakening**. The client starts a new session on the platform detected from your environment. `EINHERJAR_PLATFORM=claude|opencode` overrides that detection.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model haiku"` → TARGET=`3f8a2b1c-...`, MODEL=`haiku`
- `"ses_eac06c991ffd..."` → TARGET=`ses_eac06c991ffd...`, MODEL=`""`

### Step 2: Construct Structured Prompt

Fill this template based on the current task context. All fields are required:

```
## Theme
[Short label for the fleet registry — e.g., "user auth middleware", "inventory tags UI"]

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

Run the fleet client's background form:

```bash
einherjar delegate "[Name|SessionRef]" --prompt "[structured prompt]" --theme "[theme]" [--model <value>]
```

It writes the session row, starts the turn detached with its output captured, prints the session ref, and returns immediately. There is no harness-specific background flag: the detachment belongs to the client, so it behaves the same on Claude Code and OpenCode.

### Step 4: Continue Working

Do not block. Continue your own work.

Keep the ref from the command's output. When you need the delegated turn's result:

```bash
einherjar result <SessionRef>
```

That prints the captured output. The registry row shows the same session as `active` until the detached turn closes it.

To close a completed session on purpose: `einherjar wrap-up <SessionRef>`

---
