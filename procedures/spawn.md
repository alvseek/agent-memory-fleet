# Spawn

Start a fresh, anonymous agent session: no fleet agent name, no awakening, no presumed identity.
The fleet client records the consult, starts a new session on the platform this machine runs, and
either waits for it or returns its ref immediately. Reach for it when the work is self-contained and
does not belong to a named teammate.

A spawn is the same turn machinery as `/ask-agent` and `/delegate-agent` with the awakening left
out. Use those when a named fleet agent's specialty and memory are the point.

## Before you start

Two things must be true on this machine, and neither is checked by the spawn itself:

- **The client is installed.** Read the install resource this server serves —
  `resource://client/install` as an MCP resource, or the `read_resource("client-install")` tool —
  and follow it. It reports the current wheel URL, its hash and the exact
  `uv tool install --force` command for this deployment. Install from that URL, never from a
  repository. If `einherjar` is missing from `PATH`, report the instruction you read instead of
  proceeding.
- **This machine is signed in.** `einherjar login` completes one browser sign-in, asking for consent
  explicitly so the issuer grants `offline_access` and issues a refresh token; the client renews the
  access token on its own, so another sign-in is only needed once that stored credential expires or
  is revoked. Signing in is about tracking, not execution: the turn is a local process either way, so
  a registry `401` does not stop the spawn or lose its reply — it leaves the row buffered. Sign in to
  replay that tracking, and read the session's own output before deciding anything failed.

`einherjar install --harness claude|opencode` is the one-time per-harness setup: it registers the
MCP server that serves this procedure and removes the skills the old installer left. No copy of
these procedures is installed anywhere.

## Arguments

`$ARGUMENTS`

- `/spawn` → Construct the structured task prompt, then start one anonymous session
- `/spawn` takes no target: there is no agent to name and nothing to resume. To continue an
  existing session, use `/ask-agent <SessionRef>`.

If no arguments were provided, ask what the task is, then continue at Step 2.

---

## Procedure

### Step 1: Confirm This Is a Spawn

Choose `/spawn` when the work is self-contained, or when you specifically do not want an awakening
instruction added to the prompt. Choose `/ask-agent` or `/delegate-agent` when a named fleet agent
should act, because those are the forms that awaken one; a spawn supplies no fleet agent name, so
no teammate domain, roster entry or memory is involved.

Anonymous is not unconstrained. The spawned session still runs inside the platform's system
instructions and the project's rules, and it inherits whatever integrations that harness has
configured. It simply has no fleet identity and no presumed memory of its own.

### Step 2: Construct the Task Prompt

Fill this template. All four fields are required:

```
## Theme
[Short label for the registry row — e.g., "review the retry policy"]

## Context
[What this work is part of, and anything the session needs in order to start]

## Request
[The task itself: specific and bounded]

## Expected Output
[What to return — format, detail, and how you will judge it]
```

Two things this prompt cannot rely on: a memory the session does not have, and instructions you
only said out loud. Write them down.

When the task is long, multi-paragraph, or contains code, put it in a task file and pass a short
single-line prompt that names the file:

```bash
einherjar spawn --prompt "Read the complete task in C:/Work/IM/project/tasks/review-retry.md and follow it exactly." --theme "retry review"
```

That is the safe form on Windows, where a multiline `--prompt` passed through a command shim can
arrive truncated: the long text is read from a file the session can open, and only a short
single-line argument crosses the shell. The argument is still quoted by the shell — the truncation
affects long multiline values, so a short line is what removes the risk, not quoting as such. Check
that the session actually read the file before treating missing detail as its mistake.

### Step 3: Start It

Foreground, when your next step depends on the result:

```bash
einherjar spawn --prompt "[structured prompt]" --theme "[theme]" [--model <value>]
```

Background, when the work can run alongside your own:

```bash
einherjar spawn --background --prompt "[structured prompt]" --theme "[theme]" [--model <value>]
```

Both forms print the session ref first. The foreground form then prints the turn's envelope — its
platform, status, byte count, timings and where the log lives — and the reply after it. The background
form prints the ref alone and returns immediately, while the envelope and the log are written as the
turn runs. `--theme` is what makes the row findable later, so pass something short and stable; on
OpenCode it also becomes the session's title.

Naming no model is the normal case. On OpenCode the turn runs on the fleet's model, DeepSeek V4.1
Flash (`opencode-go/deepseek-v4.1-flash`), because a spawned session inherits none; on Claude Code
the flag is left off and the platform default applies. A bare alias on OpenCode is looked up in
`EINHERJAR_MODEL_<ALIAS>`, and an unmapped one sends no model at all — pass `provider/model` when
you need something specific.

The platform is detected from your environment: OpenCode sets `OPENCODE=1`, Claude Code sets
`CLAUDECODE=1`, and `EINHERJAR_PLATFORM=claude|opencode` overrides both. The ref tells you which one
you got: a `ses_...` value is OpenCode, a UUID is Claude Code.

### Step 4: Read the Result

Keep the ref — it is how you come back, in either mode. Every turn appends its reply to that ref's
log, and `result` reads it:

```bash
einherjar result <SessionRef>          # the last turn: its envelope, then the reply
einherjar result <SessionRef> --full   # the log: every reply this session has produced
```

A background turn writes two files as it runs — the envelope (`<ref>.result.md`) and the log
(`<ref>.out`) — so its answer is read here rather than from the command that started it. The
envelope's `status:` is where a failed turn says so: the ref is printed before the turn starts, so
the exit code cannot report how it ended, and a failure's harness error rides in `error:`.

A foreground turn prints that same envelope and reply on stdout and appends the same log, but writes
no envelope file, so `result` falls back to the log for it.

`no recorded output for <ref>` is a different answer: this machine holds no file for that ref at all.
The ref is wrong, the turn ran on another machine, or it produced no reply. It is not evidence that a
background turn is still running.

Whether the turn is still running is the registry's answer when it has one: `einherjar sessions`
shows the row `active` until the turn ends. If tracking is buffered — an outage, or a `401` — the row
can be missing or stale, so treat the status as a useful signal, never as proof.

### Step 5: Continue the Same Session

```bash
einherjar ask <SessionRef> --prompt "[next request]" --theme "[theme]"
```

Passing a ref resumes that conversation without adding an awakening, exactly as it would for a named
agent. Passing a name would start a different, awakened session instead.

Do not run overlapping turns against one session. One turn at a time per ref: wait for the foreground
reply, or for the background turn to finish — its output stops changing, and the row, when it is
recorded, leaves `active` — before sending the next request. Two turns racing in one session do not
corrupt the registry, but their answers interleave and neither is trustworthy.

## Ending the Session

A spawn ends itself: when the turn returns, the row is closed `completed`, or `failed` with the
harness's error attached. Nothing is owed afterwards.

A successful turn is not a memory wrap-up. An anonymous session has no presumed fleet identity, so
there is no teammate memory to save, and nothing here should claim one was: `completed` means the
process exited zero and its text came back, not that anything was remembered. Keep whatever the work
produced as a file or a project record, the way you would for your own work. `einherjar wrap-up
<ref>` exists for awakened fleet agents; do not use it to imply an identity this session does not
have.

## When It Goes Wrong

- **`401` or "authentication required"** — the token expired. The turn still ran and its reply is
  still there: read it (`result` for a background ref, or the foreground reply you already have)
  before deciding anything failed. Run `einherjar login` to restore tracking and replay the buffered
  row, then look at the row's status. Do not repeat the spawn for this reason — repeating one that
  already completed duplicates the work.
- **The turn fails immediately** — the client prints the harness's stderr and closes the row
  `failed`. `einherjar sessions --status failed` finds it. A missing harness on `PATH` and a model
  the harness refuses both look like this.
- **The prompt looks truncated** — a long multiline value reached the session incomplete. Start it
  again from a task file with a short instruction that points at it, rather than retrying the same
  multiline form.
- **`no recorded output`** — this machine has no file for that ref: a typo, another machine, or a turn
  that produced no reply. Check the ref and `einherjar sessions` rather than reading it as "still
  running".
- **A target was passed by mistake** — `einherjar spawn` takes none, so the extra argument is
  refused. Use `/ask-agent <Name>` for an awakened consult.

---
