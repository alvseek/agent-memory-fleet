# Ask Agent

Send a blocking consultation request to a named agent, an existing session, or an anonymous worker. The fleet client records the consult and returns its reply. Only a new named target receives the served coding awakening. The calling agent constructs the prompt and sends it without redundant user confirmation.

A consult and a delegation use the same blocking client turn. This procedure waits directly; `/delegate-agent` runs it through a completion-aware platform background task. Use this form when the next step depends on the answer.

## Before you start

Two things must be true on this machine, and neither is checked by the consult itself:

- **The client is installed.** Read the install resource this server serves —
  `resource://client/install` as an MCP resource, or the `read_resource("client-install")` tool —
  and follow it: it reports the current wheel URL, its hash and the exact
  `uv tool install --force` command for this deployment. Install from that URL, never from a
  repository. If `einherjar` is missing from `PATH`, report the instruction you read instead of
  proceeding.
- **This machine is signed in.** `einherjar login` opens the browser at `auth.lok.quest`, returns to `http://127.0.0.1:8123/callback`, and asks for consent explicitly: the issuer withholds `offline_access` without that prompt, so consent is what makes it issue a refresh token. The client keeps that token and renews the access token on its own; sign in again only when the stored credential has expired or been revoked. A `401` therefore means the stored sign-in is no longer usable: sign in again. It does not abort the consult itself — it only leaves the row untracked until the next signed-in call.

`einherjar install --harness claude|opencode` is the one-time setup per harness: it registers the MCP server that serves this procedure and removes the skills the old installer left. No copy of these procedures is installed anywhere.

## Arguments

`$ARGUMENTS`

- `/ask-agent [Name|SessionRef]` → Construct structured prompt, then send to the target agent
- `/ask-agent` → Plain `/spawn` without identity; ask for the task only if it is missing

An omitted target is not an error and does not prompt for an identity. Follow `spawn` with the task and requested model; do not treat a task description as an agent name.

---

## Procedure

### Step 1: Resolve Target

Parse the argument:
- If no identity or session ref was supplied, use anonymous spawn with no awakening.
- If it is a session ref, this is a **resume**. A UUID (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) is a Claude Code session; a `ses_...` value is an OpenCode session. The ref's own shape decides which platform the turn goes to.
- If it's a name (e.g., "Backend Django", "Software Architect"), this is a **new awakening**. The client starts a new session on the platform detected from your environment: OpenCode sets `OPENCODE=1`; Claude Code sets `CLAUDECODE=1`. `EINHERJAR_PLATFORM=claude|opencode` overrides the detection.

A name is lower-cased and hyphenated into a domain — `Software Architect` becomes `software-architect` — and that domain is what the teammate is awakened as. The client does not check a roster: the memory server is the authority on whether an agent exists, and a wrong domain fails at awakening rather than returning a polite error. When you do not know the names, `/load-fleet` reads the roster first.

Also check if `$ARGUMENTS` contains `--model <value>`. If present, extract `MODEL=<value>` and strip it from the name/ref portion before resolving the target. Examples:
- `"Backend Django --model opus"` → TARGET=`Backend Django`, MODEL=`opus`
- `"3f8a2b1c-... --model sonnet"` → TARGET=`3f8a2b1c-...`, MODEL=`sonnet`
- `"Backend Django"` → TARGET=`Backend Django`, MODEL=`""`

Without an explicit model, ordinary calls retain the existing platform defaults: the fleet's OpenCode model or Claude Code's own default. An explicit OpenCode alias must map through `EINHERJAR_MODEL_<ALIAS>` to a qualified `provider/model`; unmapped or invalid mappings fail visibly, never silently default. Carry a requested model on each resume. `/dispatch-plan` requires an explicit resolved model.

The mapping key uppercases the alias and replaces hyphens with underscores, leaving dots unchanged. Prefer a simple alias like `flash` or a qualified model. For a dotted alias in PowerShell, use the braced variable form, for example `${env:EINHERJAR_MODEL_DEEPSEEK_V4.1_FLASH} = 'opencode-go/deepseek-v4.1-flash'`.

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

For long or multiline tasks, write the structured prompt to a task file and pass a short single-line prompt naming its absolute path. Windows command shims may truncate multiline arguments even when quoted. Verify that the worker read the whole file.

### Step 3: Execute

Run the fleet client (blocking):

```bash
einherjar ask "[Name|SessionRef]" --prompt "[structured prompt]" --theme "[theme]" [--model <value>]
```

With no target, run `einherjar spawn --prompt "[structured prompt]" --theme "[theme]" [--model <value>]` instead. Set the shell tool's working directory to the project. Use a suitable supported timeout for blocking work; the default is not a fixed cap. For parallel execution follow `delegate-agent` and keep the client blocking inside the platform's notification-capable task tool.

The client records the turn then runs it; when execution returns, success prints the session ref, envelope (platform, status, byte count, timings and log path) and reply. The ref is not streamed before the blocking runner returns. Failure is reported as an error; a registry outage buffers tracking without stopping work. Use a short stable theme; on OpenCode it also titles a new session.

### Step 4: Read the Reply

Use the target agent's response to continue your work, and keep the ref from the first line (a UUID on Claude Code, `ses_...` on OpenCode). Resuming that ref with `/ask-agent [SessionRef]` sends a new prompt to the same session and records a new row; earlier rows are not overwritten. Every turn also appends its reply to that ref's log, so `einherjar result <ref>` reprints the last turn later, and `einherjar result <ref> --full` reprints every reply the session has produced.

Use the current command result to judge this turn. `result` prefers a historical envelope if present and otherwise reads the reply log; an old envelope can predate a later blocking resume. Do not run overlapping turns against one ref. Timeout or interruption is not proof the worker stopped: inspect that task/session before retrying. Process success alone does not establish task completion.

## Ending the Session

A blocking consult ends itself: when the turn returns, the row is closed `completed`, or `failed` with the harness's error attached. There is nothing to clean up after a successful `/ask-agent`, and no follow-up command is owed.

Two commands cover everything after that:

- **`einherjar sessions [--status active|completed|failed] [--project <name>]`** lists your recorded consults, one line each as ref, platform, status, theme, machine label. An empty list is a normal answer and prints `no recorded consults`.
- **`einherjar wrap-up <ref>`** concludes a session on purpose. It resumes that teammate with a wrap-up instruction, records that turn as its own row themed `wrap-up`, and closes it. Reach for it when the teammate's own memory should be saved, not merely to tidy the list — the earlier row already reflects what happened.

Do not request identity memory wrap-up for an anonymous spawned session. Keep any explicit human approval or STOP gate in the assigned task.

## When It Goes Wrong

- **`401` or "authentication required"** — the token expired. The consult still ran and its reply is already in front of you: a `401` affects tracking, not the turn. Run `einherjar login` to restore tracking and replay the buffered row, then check the row's status. Do not repeat the consult for this reason — repeating one that already completed duplicates the work.
- **The turn fails immediately** — the client prints the harness's stderr and closes the row `failed`. `einherjar sessions --status failed` finds that row again. A missing harness on `PATH` and a model the harness refuses both look like this.
- **The reply never comes** — the client waits up to five minutes for a sign-in callback only at login; a consult waits for the turn itself, so a hung turn is a hung harness. Check the ref with `einherjar sessions` before assuming the row was never written.

---
