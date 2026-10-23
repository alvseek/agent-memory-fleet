# Delegate Agent

Send a background delegation request to another specialized agent. The fleet client records the consult, awakens the target through the served coding overlay, starts the turn detached, and returns immediately. The caller continues its own work while the target works. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

A delegation and a consult are the same turn, and the difference is only whether you wait: this one prints a ref and returns, `/ask-agent` holds until the answer arrives. Delegate when the work can run alongside your own, and consult when your next step depends on the answer.

## Before you start

Two things must be true on this machine, and neither is checked by the delegation itself:

- **The client is installed.** `einherjar` on `PATH`, installed from the source repository: `uv tool install git+https://github.com/alvseek/einherjar-server`. There is no package index for it, so a bare `uv tool install einherjar` cannot work. If the command is missing, report that line instead of proceeding.
- **This machine is signed in.** `einherjar login` opens the browser at `auth.lok.quest` and returns to `http://127.0.0.1:8123/callback`, then prints the token's expiry. The token lasts an hour and this client is issued no refresh token, so a `401` means sign in again. A delegation started near the end of that hour still runs — the turn is a local process once it is spawned — but the `result` read an hour later needs a fresh sign-in.

`einherjar install --harness claude|opencode` is the one-time setup per harness: it registers the MCP server that serves this procedure and removes the skills the old installer left. No copy of these procedures is installed anywhere.

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

A name is lower-cased and hyphenated into a domain — `Backend Django` becomes `backend-django` — and that domain is what the teammate is awakened as. The client does not check a roster: a wrong domain fails at awakening. When you do not know the names, `/load-fleet` reads the roster first.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model haiku"` → TARGET=`3f8a2b1c-...`, MODEL=`haiku`
- `"ses_eac06c991ffd..."` → TARGET=`ses_eac06c991ffd...`, MODEL=`""`

Naming no model is the normal case: on OpenCode the client runs the delegated turn on the fleet's model, DeepSeek V4.1 Flash (`opencode-go/deepseek-v4.1-flash`), because a spawned turn inherits no session and therefore no model. On Claude Code the flag is left off and the platform default applies. A bare alias on OpenCode is looked up in `EINHERJAR_MODEL_<ALIAS>`, and an unmapped one sends no model at all.

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

It writes the session row, spawns the turn detached with its output captured in the client's own state directory, prints the session ref, and returns immediately. There is no harness-specific background flag: the detachment belongs to the client, so it behaves the same on Claude Code and OpenCode. `--theme` is what makes the row findable later, so pass something short and stable.

### Step 4: Continue Working

Do not block, and do not sleep waiting for it. Continue your own work; the delegated turn is a separate process with its own session.

### Step 5: Collect the Result, Then End It

```bash
einherjar result <SessionRef>
```

That prints the captured output. Until the turn has written it, it answers `no recorded output for <ref>` and exits 1, so treat that as "not finished yet" rather than a failure, and read it again later.

`einherjar sessions [--status active|completed|failed] [--project <name>]` is how you tell which case you are in: the row reads `active` while the detached turn runs and is closed `completed` or `failed` when it ends, with the harness's error attached to a failure. The list prints ref, platform, status, theme and machine label, in that order.

## Ending the Session

A delegation ends itself too: when the detached turn returns, the row is closed and the output is readable. Nothing is owed after that.

`einherjar wrap-up <ref>` is the deliberate close. It resumes that teammate with a wrap-up instruction, records that turn as its own row themed `wrap-up`, and closes it. Use it when the teammate's own memory should be saved, not merely to tidy the list — the earlier row already reflects what happened.

## When It Goes Wrong

- **`401` or "authentication required"** — the token expired. Run `einherjar login` and repeat the command; a row that could not be written is buffered and flushed on the next call, so the intended consult is not lost.
- **The turn fails immediately** — `result` still prints whatever was captured, and the row is `failed` with the harness's stderr attached. `einherjar sessions --status failed` finds it. A missing harness on `PATH` and a model the harness refuses both look like this.
- **The row never appears** — a registry that cannot be reached is buffered rather than dropped; the buffered row flushes on the next authenticated call, so `sessions` may show it later than the delegation itself.

---
