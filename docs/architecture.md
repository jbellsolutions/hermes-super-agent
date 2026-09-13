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

Optional VPS/commercial expansion:

Hermes on VPS ────────────┬──────────── Codex CLI on VPS
                          ├──────────── Docker services / MCP servers
                          ├──────────── browser-use / CDP browser
                          ├──────────── Agent Zero container (optional)
                          └──────────── Orgo AI-style managed computer (premium optional)
```

## Component roles

### Hermes Agent

Mission control. Runs from Telegram and has direct access to tools, shell, browser, files, memory, skills, subagents, cron, and messaging.

### Codex CLI

Focused coding execution engine. Best used inside git repos/worktrees for implementation, refactoring, reviews, and test-driven changes.

### Agent Zero

Visual/autonomous layer. Runs in Docker with a browser UI. Good for watching workflows, experimenting with agent profiles/plugins, and using A0 for host work.

Reproduction runbook: [`runbooks/agent-zero.md`](../runbooks/agent-zero.md).

### A0 CLI Connector

Bridge between Agent Zero and the Mac host. Provides Agent Zero with remote host file editing and command execution.

Reproduction runbook: [`runbooks/a0-connector.md`](../runbooks/a0-connector.md).

### Optional cloud computer

Managed cloud computers such as Orgo AI are not baseline dependencies. They are premium/conditional runtimes for VPS or customer deployments that need an isolated visible desktop, persistent browser GUI, or customer-specific machine boundary. See [`cloud-computer-options.md`](./cloud-computer-options.md).

### Docker/Colima

Local service runtime. Runs Agent Zero and can host future local databases, dashboards, MCP services, or sandbox apps.

## Trust and safety model

- Agent Zero UI is bound to localhost: `127.0.0.1:5080`.
- A0 connector has Read&Write and Code Execution enabled; use intentionally.
- Codex should operate inside git repos/worktrees where changes are reversible.
- Production deployment/push operations require explicit approval.
- Secrets should stay in `.env` or auth files, not docs or prompts.
- Cloud-computer providers should be isolated per customer/workspace and gated by cost controls.
