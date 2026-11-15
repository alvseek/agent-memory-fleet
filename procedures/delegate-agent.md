# Delegate Agent

Hand a task to a named or anonymous worker while retaining completion delivery to the invoking agent. The client command stays blocking; the invoking platform's background task reports when it finishes. No independent detached process or polling loop is used.

## Arguments

`$ARGUMENTS`

- `/delegate-agent [Name|SessionRef] [--model <value>]` sends a structured task.
- No target means plain `/spawn`, without an identity or awakening. Ask for a task only if the task itself is missing; do not ask which identity to use.
- A UUID or `ses_...` ref resumes its owning platform's existing conversation without another awakening. A named domain creates a new awakened session.

## Before starting

Read `resource://client/install` or `read_resource("client-install")` for the running server's current wheel, hash and exact `uv tool install --force` command. Install or upgrade only with authorization; if `einherjar` is absent from PATH, report the instruction and blocker.

`einherjar install --harness claude|opencode` registers the server, not a local copy of these procedures. `einherjar login` asks for consent to grant offline access; the stored refresh token renews access tokens until it expires or is revoked. A registry 401 affects tracking, not the worker's execution, and does not justify dispatching the task twice. Restoring sign-in replays buffered tracking; reading a local result needs no sign-in.

## 1. Resolve target and task

Follow `ask-agent` for target/model resolution and the named-or-anonymous command choice. Extract `--model` before resolving a name/ref. Use a qualified OpenCode `provider/model` or a configured alias; an unresolved explicit model fails rather than silently using a default.

Use a structured task file containing:

```markdown
## Theme
<short stable label>
## Context
<working directory, purpose and required background>
## Task
<specific work>
## Acceptance Criteria
<what completion must prove>
## Expected Deliverables
<files/results and concise final reply>
## Constraints
<scope, permissions, human gates and ownership>
```

For long or multiline tasks, pass a short single-line prompt naming the full task file; Windows shims can truncate a multiline argument. The new worker cannot rely on the invoking conversation's unsent instructions.

## 2. Execute through the platform task facility

Choose a blocking command:

```sh
einherjar ask "<Name|SessionRef>" --prompt "Read the complete task at <absolute task path> and follow it." --theme "<theme>" [--model <value>]
```

With no target, use the anonymous command:

```sh
einherjar spawn --prompt "Read the complete task at <absolute task path> and follow it." --theme "<theme>" [--model <value>]
```

Run it in the project's working directory through the invoking platform's completion-aware background shell tool:

- OpenCode: `shell` with `background: true` notifies this session when the blocking command finishes.
- Claude Code: use the available Bash/PowerShell `run_in_background` option only when it delivers completion to this conversation; respect its task lifetime/timeout rules.
- Without a notification-capable facility, keep the command blocking with an appropriate supported timeout. Do not use client detachment, an independent process, a bare shell `&`, sleep, or polling.

The removed CLI forms `einherjar delegate` and `spawn --background` must not be used. Migration means running blocking `ask` or `spawn` inside the platform task, not moving the detached child into another wrapper.

Keep the platform task handle. Continue independent work while it runs, or end this turn so the completion event can resume you. Do not poll or abandon responsibility for collecting the result.

## 3. Receive and inspect completion

On the completion notification, read the current command output: success returns the worker ref followed by its envelope and reply; failure returns an error. Keep the worker ref separately from the platform task handle. A successful turn is not proof the requested deliverable is finished: check its acceptance criteria and evidence.

If output is retained in a file, read the necessary result from that file without ingesting a raw event stream. Local `einherjar result <ref>` and `result <ref> --full` read historical output, not current running state. A legacy `.result.md` may be older than the latest blocking resume; judge the current turn by its command result.

To continue, use blocking `einherjar ask <SessionRef>` through the same platform task mechanism. Keep an explicit model on continuations. Do not run overlapping turns against the same ref.

On timeout, interruption or missing completion, inspect the existing task/session before retrying. No result is not proof the worker stopped, and stale/missing registry tracking is not proof a turn failed. A registry 401 never warrants repeating completed work.

## Ending the session

The blocking turn closes its registry row `completed` or `failed`; a tracking outage buffers updates. That status describes the process, not saved memory or accepted task completion.

`einherjar sessions` lists recorded turns. Only explicitly request `einherjar wrap-up <ref>` for a named agent whose own memory should be saved. Anonymous spawn has no presumed fleet memory and must not be wrapped up as an identity. Completion delivery depends on the invoking platform session remaining available; do not promise a notification survives its closure.
