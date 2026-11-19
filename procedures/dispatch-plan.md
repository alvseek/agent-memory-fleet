# Dispatch Plan

Execute an approved plan by coordinating implementation: delegate phases and longer tasks, handle simple fixes yourself, and verify progress before continuing.

## Arguments

`$ARGUMENTS`

```text
/dispatch-plan --plan "<plan-path>" --rules "<rules-path>" --model "<model>" --agent "<agent>"
```

- `--plan`: use this approved plan; otherwise use the plan established in the conversation.
- `--rules`: read these additional instructions fully and apply them while coordinating implementation. Rules may extend this procedure and override any argument except `--plan`.
- `--model`: use this model for delegated work.
- `--agent`: optionally use this fleet identity; otherwise spawn without an identity.

Resolve missing or conflicting instructions before starting the affected work.

## Execute

1. **Load the context.** Read the full plan and any supplied rules. Load the plan's originating wizard procedure and the coding layer's `implement-plan` procedure, and read any parent plan or project instructions required by the selected plan.

2. **Follow the plan.** Use its Execution Protocol and implementation log as the source of truth. Start with the next unfinished step whose approval and STOP gates are cleared.

3. **Choose the execution size.** Delegate a phase or longer task through the fleet's `ask-agent` procedure, using the selected model and optional identity. An omitted identity means an anonymous worker, not a request to choose an agent. Handle simple fixes yourself. Follow the supplied rules when they specify a different division of work.

4. **Give a focused assignment.** Tell the worker:
   - Which plan to read.
   - Which phase, step or longer task to execute.
   - To load and follow the coding layer's `implement-plan` procedure.
   - Any necessary context not already included in the plan.
   - Any additional rules relevant to its assignment.

   Do not invent a custom command or rewrite the implementation procedure. Apply coordination instructions yourself; give the worker the instructions it needs for its assigned work.

   When custom rules instruct you to delegate, apply those instructions yourself. Do not pass them on as instructions for the worker to delegate again. Pass only the assigned work and applicable implementation rules. Further delegation requires an explicit instruction permitting it for that worker.

5. **Supervise and verify.** Read the worker's result, inspect its changes and verification evidence, and check the plan's implementation log. A completed worker turn does not by itself mean the assignment is complete. Continue the same worker when its assignment needs further work; do not launch overlapping work on the same files.

6. **Continue or escalate.** Handle routine in-scope corrections and proceed through the plan without asking for confirmation at each phase. Stop for blockers, unclear requirements, explicit human gates or decisions costly to reverse.

7. **Report completion.** Summarize what was implemented, what was verified and what remains unfinished or unverified. Completion does not authorize release, merge or archive.
