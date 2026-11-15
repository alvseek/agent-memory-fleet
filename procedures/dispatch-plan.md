# Dispatch Plan

Hand an approved implementation plan and custom rules to a worker on an explicitly selected model, then supervise the same worker until the plan is complete or a human decision is required. Announce the resolved assignment and start without asking for confirmation again.

## Arguments

`$ARGUMENTS`

```text
/dispatch-plan plan.md rules.md
/dispatch-plan rules.md plan.md --model provider/model
/dispatch-plan --plan plan.md --rules rules.md --model provider/model --agent software-architect
/dispatch-plan --plan "<plan-path>" --rules "<rules-path>" --model provider/model --worktree "<new-path>" --branch "<new-branch>" [--base "<ref>"]
```

These are procedure inputs interpreted by the invoking agent, not a new `einherjar` CLI command.

- `--plan` and `--rules` explicitly identify the documents. With positional paths, read their contents to determine roles; either order works when unambiguous. Do not guess from filenames alone. Ask if roles remain ambiguous.
- `--model` selects the model; `--agent` optionally selects a fleet identity. They override defaults in the rules document, never requirements fixed by the approved plan.
- Rules are plain Markdown instructions. An optional YAML header works too; YAML is not required and no parser installation is needed. For example, “Use model provider/model. Use agent software-architect.” is sufficient.
- A missing model requires clarification before launch. No named agent means anonymous spawn, not a request to choose an identity.
- There is no mode setting. Parallelism uses the platform's completion-aware task facility, never client-owned detached execution.
- `--worktree` and `--branch` together request a new worktree and new branch; `--base` optionally selects their starting ref, defaulting to the source repository's current `HEAD`. Reject a partial pair or `--base` without the pair. Without these options or a recorded workspace to resume, preserve the existing working directory and branch. These are procedure options, not flags to pass to the Einherjar CLI.

## Before starting

Read both documents fully in your own context, recovering any explicitly truncated output before proceeding. Verify their paths and the working directory that owns the work. This invocation authorizes implementing an already-approved plan; it does not approve an unfinished plan or erase an outstanding human gate.

Read the fleet's `spawn`, `ask-agent` and `delegate-agent` procedures as relevant using the declared fleet access. This server serves them through `read_procedure(name)`. Verify the local client prerequisite from `resource://client/install` or `read_resource("client-install")`: the resource reports the current wheel hash and exact `uv tool install --force` command. Do not silently install or upgrade; if the client is absent, report the command and blocker. Credentials renew with a refresh token after `einherjar login` grants offline access through consent. A registry 401 affects tracking, not execution: read existing output before retrying work.

## 1. Resolve the assignment

Identify the plan, extra rules, explicit model, optional identity and project working directory. Read prose and any YAML header together. Explicit invocation values override document defaults; conflicting requirements, genuinely contradictory instructions or a missing model are questions to resolve, not opportunities to invent defaults. A rules document cannot silently replace the approved plan's scope or waive a human STOP.

Use the platform's actual model vocabulary. On OpenCode pass a qualified `provider/model`, or an alias whose `EINHERJAR_MODEL_<ALIAS>` mapping resolves to one. An unresolved or refused model is a failure to report, never permission to substitute a different model. Keep that model on every continuation.

Aliases are uppercased with hyphens replaced by underscores; dots are preserved. Use a simple alias or a qualified model where possible. Dotted environment-variable names require the braced PowerShell form, such as `${env:EINHERJAR_MODEL_DEEPSEEK_V4.1_FLASH} = 'opencode-go/deepseek-v4.1-flash'`.

### Prepare the worker's workspace

The supervisor prepares a requested worktree before launching the worker. For a recorded workspace, use the resumption checks rather than creating it again. With neither a request nor a recorded workspace, skip worktree setup and retain the existing directory and branch. Resolve the original plan and rules to absolute paths from the invoking working directory first. Those originals remain authoritative: the worker updates only the original plan's execution log, never a checkout copy. Implementation-file references resolve from the worker's implementation workspace, not from the original plan's directory.

- Inspect the source with `git rev-parse --show-toplevel`, `git status --short` and `git worktree list --porcelain`. Use that repository even if it is a submodule; do not silently move to its parent. Uncommitted changes are not carried into the new worktree. Leave them untouched: no automatic stash, commit or copy. If the approved implementation requires uncommitted source code, STOP and ask.
- Resolve the destination to an absolute path from the invoking working directory and quote paths containing spaces. Validate the branch with `git check-ref-format --branch`. Refuse an existing destination, existing local branch or conflicting registered worktree; never overwrite, reset or force. Resolve the requested base or source `HEAD` using `git rev-parse --verify --end-of-options "<base>^{commit}"` and retain the exact starting commit. Do not fetch or substitute a default branch.
- Create with `git -C "<source-root>" worktree add -b "<new-branch>" "<absolute-worktree-path>" "<resolved-base-commit>"`. Check success, then immediately record the source root, worktree path, branch, exact starting commit and original document paths in the execution context and existing plan log, before further setup.
- Run `git -C "<absolute-worktree-path>" submodule update --init --recursive`. Initialize pinned commits, not newer remote tips. Verify the registered worktree, repository identity, actual branch and starting commit, and check recursive submodule status for incomplete initialization or mismatched pins before launching. Do not automatically copy secrets, `.env` files or dependency folders. Worktrees do not isolate databases or ports; use project-approved configuration and ask if required setup is missing.
- On resumption, verify the recorded source repository, registered path, branch, original document paths and starting commit. Compare the source and target's absolute `git rev-parse --path-format=absolute --git-common-dir` results to establish repository identity, and check the actual branch with `git branch --show-current`. The worker's `HEAD` may have advanced; do not reset it to the starting commit or create a second worktree. A conflicting new assignment requires clarification. If setup fails, report actual artifacts and remaining setup, STOP without launching a worker, and never automatically remove the worktree or branch.

## 2. Prepare the handoff and announce it

Write a durable task file in a suitable project/task location or approved temporary directory. Include all of these fields:

```markdown
## Theme
<short stable task label>

## Context
<absolute implementation working directory, approved scope, resolved model and identity or anonymous;
when using a worktree: source repository, worktree path, branch and exact starting commit>

## Task
Read the full plan at <absolute plan path> and full rules at <absolute rules path>.
Load and follow the coding layer's implement-plan procedure.
Use the assigned implementation directory. If a worktree assignment is supplied,
it is already prepared: verify it and do not create another worktree.
Keep the original plan/rules authoritative and update only the original plan's execution log.
Implement sequentially, verify each step and update the plan's execution log.

## Acceptance Criteria
<the plan's completion requirements, evidence expected and human gates>

## Deliverables
<files or outputs owned by this worker, plan/log paths>

## Constraints
<custom rules, supervisor authority, explicit STOP/sign-off requirements and escalation>

## Expected Output
<completed steps, tests and evidence, remaining work, blockers/decisions,
updated plan/log paths and a concise final conclusion>
```

Resolve coding-layer access explicitly in this handoff: under `[PROJECT-ACCESS] = mcp`, the worker fetches `read_procedure("implement-plan")` from Hermod and follows it; under markdown, load the installed implement-plan procedure. Do not replace that procedure with a paraphrase. Require full plan/rules reads before implementation, including recovery from observed truncation.

Assign exclusive ownership of implementation paths and the original plan log to the worker while its turn runs. Do not edit them concurrently as supervisor. The plan/log remains the implementation source of truth; the rules document constrains execution rather than becoming a second progress tracker. When using a worktree, implementation files belong there, not in the source checkout; only the agreed original plan log may change in the source checkout.

Tell the user what will run: original plan and rules paths, implementation working directory, worktree branch and exact base commit when requested, selected model, named identity or anonymous worker, and that you will supervise until completion or a human gate. This is an announcement, not a confirmation prompt. Then proceed without waiting for another approval.

## 3. Start a notification-safe worker turn

Follow `delegate-agent` for platform-owned completion delivery, with a blocking client command:

```sh
einherjar ask "<agent-domain>" --model "<resolved-model>" --theme "<theme>" --prompt "Read the full task at <absolute task path> and follow it exactly."
```

With no identity, use plain spawn, with no awakening instruction:

```sh
einherjar spawn --model "<resolved-model>" --theme "<theme>" --prompt "Read the full task at <absolute task path> and follow it exactly."
```

Use a short single-line prompt naming the task file; Windows command shims can truncate long multiline values even when quoted. Use the platform shell tool's working-directory parameter, set to the prepared implementation directory for the initial launch and every continuation. A shell-only `cd` does not move the agent session. When Windows subprocess output needs it, set `PYTHONUTF8=1` for that invocation.

- OpenCode: its `shell` tool with `background: true` runs this blocking command and notifies the invoking session when it finishes.
- Claude Code: use its available Bash/PowerShell background-task option (`run_in_background`) only when that tool delivers completion back to this conversation; respect its current lifecycle/time limits.
- If no completion-aware task facility is available, remain blocking with a suitable supported timeout and read the direct result. Do not detach, use a bare shell `&`/independent process, sleep or poll for completion.

Retain the platform task handle. When the command finishes, its output includes the worker ref, turn envelope and final reply, or a failure. The task handle and worker ref are different identifiers. Do not enable raw event-stream output: use the bounded final result and full-output path.

## 4. Verify, then continue the same worker

On completion notification, read the returned output and any output file needed to recover the result. Check the worker actually read the full plan, rules and implement-plan procedure and used the assigned workspace and branch. Inspect the original plan/log, changes in the implementation directory and reported verification evidence; when a separate worktree is used, check the source checkout for unintended implementation edits. Process success means a turn ended, not that the plan is finished.

When routine in-scope work remains, send a specific correction or next task to the same worker:

```sh
einherjar ask "<worker-ref>" --model "<same-resolved-model>" --theme "<theme>" --prompt "Read the continuation task at <absolute task path> and follow it."
```

Use the same notification-safe execution mechanism and the same verified implementation directory and branch each time. Resume the ref, do not start a fresh identity session or awaken again. Do not run overlapping turns against one ref. Continue guiding without routine reconfirmation until completion or a real escalation.

`einherjar result <ref>` reads a historical envelope when present, otherwise the accumulated reply log; `--full` reads the whole log. It is not a live running flag. Following a foreground resume, an older historical envelope may describe an earlier turn: use the current command result, not stale disk metadata, to judge this turn.

On timeout, interruption, cancellation or missing output, do not assume the worker stopped. Inspect the existing platform task/session and plan before any continuation or retry. Do not start a duplicate turn merely because notification did not arrive. A closed invoking session cannot be promised later delivery; recover its task/ref/evidence before resuming.

## 5. Escalate or finish

Handle routine implementation and in-scope review fixes as supervisor. Return to the user for blockers, scope changes, explicit human STOP/sign-off gates or a decision costly to reverse, such as durable data or an externally depended-on contract. Do not silently waive quality-review approval or archive sign-off. Present the exact issue, options and evidence, then wait.

Declare the plan complete only against its actual requirements and verification. State what changed, what was tested, and what remains unverified or explicitly deferred. Include the worktree path and branch in the result when used. Do not archive, merge, remove a worktree or delete its branch without human sign-off. Anonymous workers have no presumed identity memory: do not send them `einherjar wrap-up`. Named agents may save their own memory only when that is explicitly requested; a completed turn alone does not mean memory was saved.
