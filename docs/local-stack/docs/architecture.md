# Architecture

## High-level architecture

```text
Telegram
   │
   ▼
Hermes Agent ─────────────┬──────────── Codex CLI
   │                      │
   │                      ├──────────── Local filesystem / shell
   │                      │
   │                      ├──────────── Browser automation
   │                      │
   │                      └──────────── Docker / Colima
   │
   └── manages/checks ──── Agent Zero container
                              │
                              ▼
                        Agent Zero Web UI
                              │
                              ▼
                       A0 CLI Connector
                              │
                              ▼
                    Host Mac /Users/home / codex
```

## Component roles

### Hermes Agent

Mission control. Runs from Telegram and has direct access to tools, shell, browser, files, memory, skills, subagents, cron, and messaging.

### Codex CLI

Focused coding execution engine. Best used inside git repos/worktrees for implementation, refactoring, reviews, and test-driven changes.

### Agent Zero

Visual/autonomous layer. Runs in Docker with a browser UI. Good for watching workflows, experimenting with agent profiles/plugins, and using A0 for host work.

### A0 CLI Connector

Bridge between Agent Zero and the Mac host. Provides Agent Zero with remote host file editing and command execution.

### Docker/Colima

Local service runtime. Runs Agent Zero and can host future local databases, dashboards, MCP services, or sandbox apps.

## Trust and safety model

- Agent Zero UI is bound to localhost: `127.0.0.1:5080`.
- A0 connector has Read&Write and Code Execution enabled; use intentionally.
- Codex should operate inside git repos/worktrees where changes are reversible.
- Production deployment/push operations require explicit approval.
- Secrets should stay in `.env` or auth files, not docs or prompts.
