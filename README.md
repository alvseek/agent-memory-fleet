# agent-memory-fleet

The **agent-fleet add-on** of the [agent-memory](https://github.com/alvseek/agent-memory-system) framework, and a member of the **Hermod family** beside the coding overlay ([agent-memory-project](https://github.com/alvseek/agent-memory-project)).

This repo holds the agent-to-agent fleet operations: consult a teammate (`/ask-agent`), hand a task off (`/delegate-agent`), read the project's roster (`/load-fleet`), and define the team (`/setup-fleet`). They run by spawning and resuming Claude Code sessions, which is a mechanism a chat agent cannot use, so the fleet is its own capability rather than part of the coding overlay or the memory core.

## Relationship to the family

- **Standalone, independent repo**: a peer of the core (`agent-memory-system`) and the coding overlay (`agent-memory-project`).
- **One-way dependency**: this repo references the core (through `[AGENT-MEMORY-PATH]` and the core's `/awaken-agent`) and reads `[PROJECT-ACCESS]` to reach the coding overlay. Neither references this repo by name.
- **Data stays central**: the fleet's roster (`fleet-agents.md`) and active-session map (`fleet-map.csv`) live in the `@agent-memory` store under `shared-memory/[project]/`, not in this repo.

## Contents

- **procedures/**: `ask-agent`, `delegate-agent`, `load-fleet`, `setup-fleet`
- **fleet-scripts/**: `ask-agent.sh`, `delegate-agent.sh`, `wrap-up-agent.sh`, `fleet-common.sh`
- **templates/**: `fleet-agents-template.md`, `fleet-map-template.csv`

## Setup

Install the **memory core first**, then this repo (and the coding overlay, which a spawned agent awakens through):

```bash
python setup-scripts/setup-all-claude-code.py
python setup-scripts/setup-all-codex.py
python setup-scripts/setup-all-antigravity.py
python setup-scripts/setup-all-opencode.py
```

On Windows, run the matching `setup-scripts\setup-all-*.bat`.

Each installer keeps its own manifest and registers `[path-to-agent-memory-fleet]` plus the `[FLEET-ACCESS]` / `[FLEET-MCP-URL]` declaration in that platform's global instructions file.

> The fleet scripts shell out to the `claude` CLI, so a spawn only runs where Claude Code is installed, even though the procedures install on every harness.

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE). See [MIGRATION.md](MIGRATION.md) for where this came from.
