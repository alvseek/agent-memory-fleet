# ADR-002: The fleet data boundary

**Date**: 2026-10-21

**Status**: Accepted

---

## Problem

The fleet kept two pieces of data in one place: the project roster (who is on the team) and the active-session map (which agent sessions exist). Both were files under the memory store, which works on a machine that has the store checked out and fails on one whose memory is served. The two pieces are not the same kind of fact. A roster is project knowledge that every session should see; a session row describes a process on one specific machine, in a session id that machine owns. Treating them alike makes the roster unavailable where it is most needed and makes the map claim reach it does not have.

---

## Decision

**We decided to**: keep the roster in the memory store as project context, and move session rows into a separate fleet service, Einherjar, which owns its own table, its own migrations and its own auth.

The roster is written by the agent through Munnin as a `knowledge` record carrying a project. That is the shape the coding overlay's roster pointer already reads, and the knowledge gates (a template stamp and a summary) apply to it. Session rows live in Einherjar's `fleet_session` table, keyed by `(user_id, machine, ref)`, written by the CLI on the user's machine. The registry is advisory for the spawn: a consult records itself there, and a registry failure buffers the row and lets the consult proceed. Remote execution is explicitly not in the model; a row says where a session lives, never how to reach into another machine.

**Why we chose this:**
- A roster is portable team knowledge; a session row is machine-local runtime state. One store for both forces one of them to be wrong.
- The overlay already reads the roster as project context, so moving it there makes the existing pointer work rather than adding a cross-service call for one lookup.
- A typed table with a natural key that carries every distinguishing axis is the only shape where two machines write independently without one losing a row.
- A service that owns its schema keeps Munnin the single owner of memory-shaped data, and keeps Hermod's no-DDL rule intact.

---

## What to Build (Requirements)

**Core Requirements:**
- A `knowledge` roster record with project, title `fleet-agents`, a one-line summary and the knowledge template's stamp, written and read by the fleet procedures.
- An Einherjar service owning `fleet_session`, with migrations applied on first connection and no DDL from any other service.
- HTTP write endpoints for the CLI and read-only MCP tools for the agent.
- Tenant resolution from the verified token's `(iss, sub)`, creating the mapping on first contact, so two users never share a row.
- A CLI that owns the machine identity, the token, the pending buffer and the local spawn.
- A deploy repository that pins the service and can roll back independently.

**Success Criteria:**
- The overlay's fleet pointer fires in a project whose roster is a served record.
- Two users see disjoint registries, including identical machine labels and ref strings.
- A consult with the service down still runs, and its row appears when the service returns.
- The service is deployed at its own host, behind the same issuer, with a token audience that matches the registered resource.

---

## Alternatives Rejected

- **Sessions as `shared_record` JSON rows in Hermod**: no DDL, but a JSON body with no typed columns, and fleet logic inside the coding server.
- **One row per project holding every session**: read-modify-write on every spawn, so two machines writing at once lose one.
- **A local map only**: no cross-machine view and no record of which machine a ref belongs to.
- **Extending Hermod with fleet routes**: either breaks its no-DDL rule or splits schema ownership across two repos.
- **A hosted service that also spawns agents**: tools run server-side, so the spawn would happen on the wrong machine.

---

**Full context**: [High Wizard plan](../../plans/2026-10-20-agent-memory-fleet-fleet-delivery.md)
