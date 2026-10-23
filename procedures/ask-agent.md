# Ask Agent

Send a blocking consultation request to another specialized agent. The fleet client records the consult, awakens the target through the served coding overlay, sends the structured prompt, and returns the reply. This procedure is designed for agent-to-agent communication — the calling agent constructs the prompt and sends it without user confirmation.

A consult and a delegation are the same turn, and the difference is only whether you wait: this one holds until the answer arrives, `/delegate-agent` returns a ref immediately. Use this form when the next step depends on the answer.

## Before you start

Two things must be true on this machine, and neither is checked by the consult itself:

- **The client is installed.** `einherjar` on `PATH`, installed from the source repository: `uv tool install git+https://github.com/alvseek/einherjar-server`. There is no package index for it, so a bare `uv tool install einherjar` cannot work. If the command is missing, report that line instead of proceeding.
- **This machine is signed in.** `einherjar login` opens the browser at `auth.lok.quest` and returns to `http://127.0.0.1:8123/callback`, then prints the token's expiry. The token lasts an hour and this client is issued no refresh token, so a `401` during a consult means sign in again, not that something is broken.

`einherjar install --harness claude|opencode` is the one-time setup per harness: it registers the MCP server that serves this procedure and removes the skills the old installer left. No copy of these procedures is installed anywhere.

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

A name is lower-cased and hyphenated into a domain — `Software Architect` becomes `software-architect` — and that domain is what the teammate is awakened as. The client does not check a roster: the memory server is the authority on whether an agent exists, and a wrong domain fails at awakening rather than returning a polite error. When you do not know the names, `/load-fleet` reads the roster first.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model sonnet"` → TARGET=`3f8a2b1c-...`, MODEL=`sonnet`
- `"Backend Django"` → TARGET=`Backend Django`, MODEL=`""`

Naming no model is the normal case: on OpenCode the client runs the turn on the fleet's model, DeepSeek V4.1 Flash (`opencode-go/deepseek-v4.1-flash`), because a spawned turn inherits no session and therefore no model. On Claude Code the flag is simply left off, so the platform default applies. A bare alias on OpenCode is looked up in `EINHERJAR_MODEL_<ALIAS>`, and an unmapped one sends no model at all — pass `provider/model` if you need something specific.

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

The client writes the session row first, then spawns the turn, so a failed spawn still leaves a row saying so. The command's first stdout line is the session ref; the reply follows it. Pass `--theme` with something short and stable: it is what makes the row findable later.

### Step 4: Read the Reply

Use the target agent's response to continue your work, and keep the ref from the first line (a UUID on Claude Code, `ses_...` on OpenCode). Resuming that ref with `/ask-agent [SessionRef]` sends a new prompt to the same session and records a new row; earlier rows are not overwritten.

## Ending the Session

A blocking consult ends itself: when the turn returns, the row is closed `completed`, or `failed` with the harness's error attached. There is nothing to clean up after a successful `/ask-agent`, and no follow-up command is owed.

Two commands cover everything after that:

- **`einherjar sessions [--status active|completed|failed] [--project <name>]`** lists your recorded consults, one line each as ref, platform, status, theme, machine label. An empty list is a normal answer and prints `no recorded consults`.
- **`einherjar wrap-up <ref>`** concludes a session on purpose. It resumes that teammate with a wrap-up instruction, records that turn as its own row themed `wrap-up`, and closes it. Reach for it when the teammate's own memory should be saved, not merely to tidy the list — the earlier row already reflects what happened.

## When It Goes Wrong

- **`401` or "authentication required"** — the token expired. Run `einherjar login` and repeat the consult; nothing was lost, because a row that could not be written is buffered and flushed on the next call.
- **The turn fails immediately** — the client prints the harness's stderr and closes the row `failed`. `einherjar sessions --status failed` finds that row again. A missing harness on `PATH` and a model the harness refuses both look like this.
- **The reply never comes** — the client waits up to five minutes for a sign-in callback only at login; a consult waits for the turn itself, so a hung turn is a hung harness. Check the ref with `einherjar sessions` before assuming the row was never written.

---
