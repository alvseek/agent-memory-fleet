# Dispatch Plan

Follow the coding layer's `implement-plan` procedure on an approved plan, delegating phases and longer tasks to workers while handling simple fixes yourself.

## Arguments

`$ARGUMENTS`

```text
/dispatch-plan --plan "<plan-path>" --rules "<rules-path>" --model "<model>" --agent "<agent>"
```

- `--plan`: use this approved plan; otherwise use the plan established in the conversation.
- `--rules`: read these additional instructions fully and apply them yourself. Rules may extend this procedure and override any argument except `--plan`.
- `--model`: use this model for delegated work.
- `--agent`: optionally use this fleet identity; otherwise use an anonymous worker.

Resolve missing or conflicting instructions before starting the affected work.

## Execute

1. **Follow `implement-plan`.** Load and follow the coding layer's `implement-plan` procedure, including its context loading, the plan's originating wizard procedure and its execution protocol. The instructions below add delegation; they do not replace that procedure.

2. **Delegate substantial work.** Assign phases and longer tasks through the fleet's `ask-agent` procedure using the selected model and optional identity. Handle simple fixes yourself unless the supplied rules specify otherwise.

3. **Give a focused assignment.** Tell the worker to read the plan, execute the assigned phase or step, and load and follow `implement-plan` for that assignment. Include applicable implementation rules and only necessary context absent from the plan. Do not invent a custom command or rewrite the implementation procedure.

   Apply rules about how you delegate yourself. Do not pass them on as instructions for the worker to delegate again. Further delegation requires an explicit instruction permitting it for that worker.

4. **Supervise through completion.** Read the worker's result, inspect its changes and verification evidence, and check the plan's execution log before continuing. Resume the same worker if its assignment is unfinished. Do not overlap work on the same files or edit files a worker is changing.

5. **Continue or escalate.** Continue through the plan without routine reconfirmation. Bring blockers, unclear requirements, explicit human gates and decisions costly to reverse to [USER-NAME].

6. **Report the outcome.** State what was implemented, what was verified and what remains unfinished or unverified. Completion does not authorize release, merge or archive.
