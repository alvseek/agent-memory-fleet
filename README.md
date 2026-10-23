# agent-memory-fleet

The **fleet layer's content**: the four procedures an agent uses to consult a teammate, hand a task off, read the project's roster, and define the team, plus the roster template and the compiler that validates them.

The layer is **served, not installed**. [einherjar-server](https://github.com/alvseek/einherjar-server) vendors this repo and serves each procedure as an MCP prompt and through a `read_procedure` tool, and the roster template as a resource. Nothing here is copied into a harness's skills directory; `einherjar install` registers the server and removes anything an earlier installer left.

This repo is a member of the agent-memory family: Munnin is the memory core, Hermod the coding overlay, and Einherjar the fleet layer's server.

## Contents

- **`procedures/`**: `ask-agent`, `delegate-agent`, `load-fleet`, `setup-fleet`
- **`templates/`**: `fleet-agents-template.md`
- **`setup-scripts/compile-procedures.py`**: the compiler, kept as **CI validation**. It inlines any component reference and fails a build on an unresolved template; the served text is compared against its output.

## Setup

Install the client and point one harness at the server:

```sh
uv tool install git+https://github.com/alvseek/einherjar-server
einherjar install --harness opencode   # or: --harness claude
einherjar login
```

There is no package index for the client, so the install names its source repository. `einherjar install` registers `https://einherjar.lok.quest/mcp` in that harness and removes the skills the old markdown installer left behind. `einherjar login` is one browser step per machine, and the token it stores lasts an hour.

The memory core and the coding overlay are separate installs; a fleet agent awakens through both.

## Data

- **The roster** (`fleet-agents`) is one `knowledge` record in the project's context, written by the agent through Munnin. `setup-fleet` creates it; `load-fleet` reads it.
- **Sessions** are rows in Einherjar's own `fleet_session` table, keyed by `(user_id, machine, session_ref)`, written by the CLI on the machine where the agent runs.

## Decisions

- [ADR-001: The fleet transport contract](docs/adr/2026-10-21-fleet-transport-contract.md)
- [ADR-002: The fleet data boundary](docs/adr/2026-10-21-fleet-data-boundary.md)
- [ADR-003: The fleet layer is served, not installed](docs/adr/2026-10-21-fleet-served-layer.md)
- [The plan that built it](plans/2026-10-20-agent-memory-fleet-fleet-delivery.md)

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
