# Decision 0001: Local Multi-Agent Stack

Date: 2026-05-01

## Decision

Use Hermes as the top-level command center, with Agent Zero as a browser-visible autonomous layer, Codex as the coding execution engine, A0 Connector as the host bridge, and Docker/Colima as the local service runtime.

## Context

Justin wants a powerful local agent setup that can be controlled from Telegram, observed in a browser UI, and expanded/documented as we learn what works.

## Consequences

### Benefits

- Hermes can orchestrate everything from Telegram.
- Agent Zero gives a visible UI and plugin/skill ecosystem.
- Codex provides strong coding-agent execution.
- A0 Connector lets Agent Zero reach the real Mac host.
- Docker/Colima enables local services without Docker Desktop.

### Tradeoffs

- More moving parts to monitor.
- A0 Read&Write + Code Execution is powerful and must be treated carefully.
- Disk space needs monitoring because containers, videos, and project assets can grow quickly.

## Operating rule

Use git repos/worktrees for code changes, keep secrets out of prompts/docs, and require explicit approval before production-impacting deployments.
