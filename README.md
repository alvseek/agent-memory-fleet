# agent-memory-fleet

The **fleet layer's content**: procedures to consult a teammate, delegate with completion delivery, supervise an approved plan, start an anonymous session, read the roster and define the team, plus its roster template and validation compiler.

The layer is **served, not installed**. [einherjar-server](https://github.com/alvseek/einherjar-server) vendors this repo and serves each procedure as an MCP prompt and through a `read_procedure` tool, and the roster template as a resource. Nothing here is copied into a harness's skills directory; `einherjar install` registers the server and removes anything an earlier installer left.

This repo is a member of the agent-memory family: Munnin is the memory core, Hermod the coding overlay, and Einherjar the fleet layer's server.

## Contents

- **`procedures/`**: `ask-agent`, `delegate-agent`, `spawn`, `dispatch-plan`, `load-fleet`, `setup-fleet`
- **`templates/`**: `fleet-agents-template.md`
- **`setup-scripts/compile-procedures.py`**: the compiler, kept as **CI validation**. It inlines any component reference and fails a build on an unresolved template; the served text is compared against its output.

## Setup

The client is its own package, published by the server rather than by a package index. Read the
running server's install resource — `resource://client/install` as an MCP resource, or
`GET /v1/resources/cli` on the same server — and follow the command it reports:

```sh
uv tool install --force <the wheel URL that endpoint reports>
einherjar install --harness opencode   # or: --harness claude
einherjar login
```

That endpoint describes the one wheel bundled with the running server: its real version, size,
SHA-256, URL and install command, so what you install is current for that deployment and need not
match the server's own version. There is nothing to clone and no package index to find it in.

`einherjar install` registers the server's MCP face in that harness and removes the skills the old
markdown installer left behind. `einherjar login` is one browser step per machine: the request asks
for consent so the issuer grants offline access, and the client renews its own token afterwards.

The memory core and the coding overlay are separate installs; a fleet agent awakens through both.

## Handing off work

`ask-agent` waits for a blocking turn. `delegate-agent` runs that same blocking CLI command through the invoking platform's completion-aware background task, or remains blocking when no such facility exists. Neither relies on an independent detached process. An omitted identity in either procedure selects anonymous spawn; a session ref resumes without awakening.

`/dispatch-plan plan.md rules.md` reads both documents and announces the selected model, optional identity and assignment before proceeding without another confirmation. Rules may be plain Markdown or use an optional YAML header. Explicit `--model`/`--agent` options override document defaults, not approved plan requirements. The supervisor checks each result and continues the same worker until completion, a blocker or a human sign-off/decision gate.

CLI `delegate` and `spawn --background` have been removed. Migrate scripts to blocking `ask`/`spawn` inside a notification-capable platform shell task; do not replace them with shell detachment or polling. Historical output and refs remain readable. Other machines must explicitly upgrade their client; changing served guidance does not remove commands from old binaries.

## Data

- **The roster** (`fleet-agents`) is one `knowledge` record in the project's context, written by the agent through Munnin. `setup-fleet` creates it; `load-fleet` reads it.
- **Sessions** are rows in Einherjar's own `fleet_session` table, keyed by `(user_id, machine, session_ref)`, written by the CLI on the machine where the agent runs.

## Decisions

- [ADR-001: The fleet transport contract](docs/adr/2026-10-21-fleet-transport-contract.md)
- [ADR-002: The fleet data boundary](docs/adr/2026-10-21-fleet-data-boundary.md)
- [ADR-003: The fleet layer is served, not installed](docs/adr/2026-10-21-fleet-served-layer.md)
- [ADR-004: The invoking platform owns completion delivery](docs/adr/2026-11-15-platform-owned-completion.md) — supersedes ADR-001's client-detachment decision only.
- [The plan that built it](plans/2026-10-20-agent-memory-fleet-fleet-delivery.md)

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
