# Decision 0001: Super Agent is Agent OS plus local runtimes

## Status

Accepted.

## Context

The first `hermes-super-agent` repo was documentation-first. It tracked the local Hermes, Codex, Agent Zero, A0, Docker/Colima setup, but it did not use `jbellsolutions/agent-os` as the actual repository foundation.

Justin clarified that Super Agent should be a new version of Agent OS itself: Agent OS plus Codex and Agent Zero.

## Decision

`hermes-super-agent` is now based directly on `jbellsolutions/agent-os`.

Super Agent adds:

- Hermes as the command center.
- Codex CLI as the coding runtime.
- Agent Zero as the visual/autonomous UI runtime.
- A0 as the Agent Zero host bridge.
- Local runbooks, health checks, and setup documentation from the previous Super Agent docs repo.

## Consequences

- Agent OS files live at the repo root instead of being vendored under `third_party/`.
- Previous docs are preserved under `docs/local-stack/` and restored where useful at top level.
- Agent Zero has a runtime manifest at `src/agent_os/runtimes/agent_zero/manifest.yaml`.
- The job router can route `agent-zero`, `agent_zero`, `visual`, and `autonomous-ui` tagged work to the `agent_zero` runtime.
- The package remains source-compatible with `agent_os` while adding a `super-agent` CLI alias.
