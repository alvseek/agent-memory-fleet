# Spawn

Start a fresh anonymous worker: no fleet agent name, no awakening and no presumed memory identity. The client runs one blocking turn, records its outcome and returns the reply. Parallel work uses the invoking platform's completion-aware task facility, not an independent detached child.

## Before starting

Read `resource://client/install` or `read_resource("client-install")` for the current wheel URL, hash and exact `uv tool install --force` command. Do not silently install or upgrade. If the client is absent from PATH, report that instruction and blocker.

`einherjar login` asks for consent to grant offline access and a refresh token; access tokens renew automatically until the credential expires or is revoked. A registry 401 affects tracking only: a turn can finish while its row is buffered. Read its output before retrying; restoring sign-in replays tracking. Do not repeat the spawn just because tracking failed: that duplicates the work.

`einherjar install --harness claude|opencode` registers the served MCP layer, not local copies of its procedures.

## Arguments

`$ARGUMENTS`

`/spawn` takes a task and optional model, not an identity target. Ask what the task is only when it was not supplied. To resume an existing session, use `ask-agent <SessionRef>`; do not create a fresh worker for a continuation.

## 1. Construct a complete task

Anonymous does not mean unconstrained. The worker has no fleet identity, but still runs under its platform system instructions, project rules and configured integrations.

Fill all four fields:

```markdown
## Theme
<short stable label>
## Context
<project directory, background and relevant inputs>
## Request
<specific bounded work>
## Expected Output
<deliverables, verification evidence and concise final reply>
```

For a long or multiline task, write a task file and pass a short single-line prompt naming its absolute path. Windows command shims can truncate multiline values even when quoted. The short prompt still uses normal shell quoting; its size and single-line form remove the truncation risk. Check the worker actually read the full file.

## 2. Execute one blocking turn

```sh
einherjar spawn --prompt "Read the complete task at <absolute task path> and follow it exactly." --theme "<theme>" [--model <value>]
```

Set the shell tool's working directory to the project. The platform is detected from the environment; `EINHERJAR_PLATFORM=claude|opencode` overrides it. OpenCode uses `ses_...` refs; Claude Code uses UUID refs.

Ordinary omitted-model calls keep existing defaults (the fleet's OpenCode model, or Claude Code's default). An explicit OpenCode alias must resolve via `EINHERJAR_MODEL_<ALIAS>` to `provider/model`; an unmapped alias is refused, not silently dropped. Use a qualified model when specificity matters. `/dispatch-plan` requires an explicit resolved model.

Alias keys use uppercase with hyphens changed to underscores; dots remain. Prefer a portable short alias such as `flash`. PowerShell needs braces around a dotted variable name: `${env:EINHERJAR_MODEL_DEEPSEEK_V4.1_FLASH} = 'opencode-go/deepseek-v4.1-flash'`. Passing the qualified model avoids alias setup entirely.

The client waits for the runner. Success then prints the ref, envelope (platform, status, bytes, timings and output path) and reply, and appends the same log on disk. A failure returns a nonzero exit and error. Do not expect the worker ref to stream before the blocking runner finishes.

For parallel work, follow `delegate-agent`: run this same blocking command in OpenCode's `shell(background: true)` or a notification-capable Claude Code background Bash/PowerShell task. The platform reports completion to the invoking session. Without that facility, stay blocking with a suitable supported timeout. Never use client detachment, shell `&`, sleep or polling to fake notification. The removed CLI `spawn --background` is not an available mode.

## 3. Read and verify the result

Use the current command result, or the platform's completion output/file, to read the latest turn. Process completion is not proof the task is complete: check its expected output and verification evidence.

```sh
einherjar result <SessionRef>
einherjar result <SessionRef> --full
```

These read historical output. `result` prefers a legacy `<ref>.result.md` envelope if present, otherwise the reply log; `--full` always reads the log of every recorded reply. An old envelope may predate a blocking resume. `no recorded output` means no local file was found, not "still running". Registry status is a signal, never proof: tracking can be missing or stale when buffered.

## 4. Continue the same session

```sh
einherjar ask <SessionRef> --prompt "<next request>" --theme "<theme>" [--model <same-value>]
```

A ref resumes without awakening. A name would start a different identity session. Preserve the explicitly chosen model and use the same completion-safe execution mechanism on each turn.

Do not run overlapping turns against one ref. After timeout, interruption, cancellation or missing output, inspect the existing platform task/session and plan before retrying; absence of output does not establish that the worker stopped. Do not promise notification survives closing the invoking session.

## Ending the session

A successful turn is not a memory wrap-up. The registry row is closed `completed` when the process succeeds, or `failed` on error; a tracking failure buffers changes. This means the process ended, not that anything was remembered.

An anonymous worker has no presumed teammate memory. Do not use `einherjar wrap-up <ref>` to assign it an identity or imply memory was saved. Keep its deliverables as ordinary project artifacts. Preserve any human approval/STOP gate in the task.
