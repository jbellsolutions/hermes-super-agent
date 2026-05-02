# Inventory

_Last updated: 2026-05-02_

## Executive summary

Justin's Mac has a layered autonomous-agent stack:

1. **Hermes Agent** — Telegram-accessible orchestrator with local tool access.
2. **OpenAI Codex CLI** — authenticated coding agent for repos and reviews.
3. **Agent Zero** — Dockerized local web UI autonomous agent.
4. **A0 CLI Connector** — host bridge between Agent Zero and the Mac.
5. **Colima + Docker** — container runtime for Agent Zero and future services.

## Versions/status verified

- Hermes: `Hermes Agent v0.11.0 (2026.4.23)`
- Codex CLI: `codex-cli 0.125.0`
- A0 CLI: `1.5`
- Docker: `29.4.2`
- Docker Compose: `5.1.3`
- Colima: running, Docker runtime, macOS Virtualization.Framework, virtiofs
- Agent Zero: container `agent-zero`, running at `127.0.0.1:5080`

## Hermes enabled toolsets

Enabled:

- web search/scraping
- browser automation
- terminal/process control
- file operations
- code execution
- vision/image analysis
- image generation
- Mixture of Agents
- text-to-speech
- skills
- todo/task planning
- memory
- session search
- clarification prompts
- delegation/subagents
- cron jobs
- messaging

Disabled currently:

- RL training
- Home Assistant
- Spotify
- Yuanbao

## Agent Zero connector capabilities

Reported by `/api/plugins/_a0_connector/v1/capabilities`:

- chat create/list/get/reset/delete
- pause/nudge/message send
- log tail
- projects
- remote file tree
- remote text editing
- remote code execution
- remote computer use
- token status
- settings get/set
- agent profile set
- agents list
- skills list/delete
- model presets
- model switcher
- chat compaction

## Important paths

### Agent Zero

- URL: `http://127.0.0.1:5080`
- Container: `agent-zero`
- Data directory: `/Users/home/agent-zero/agent-zero/usr`
- Env file: `/Users/home/agent-zero/agent-zero/usr/.env`
- Reproduction runbook: `runbooks/agent-zero.md`

### A0 Connector

- tmux session: `a0`
- launchd label: `com.justin.a0-connector`
- startup script: `/Users/home/bin/start-a0-connector.sh`
- plist: `/Users/home/Library/LaunchAgents/com.justin.a0-connector.plist`
- stdout log: `/Users/home/Library/Logs/a0-connector.log`
- stderr log: `/Users/home/Library/Logs/a0-connector.err.log`
- Reproduction runbook: `runbooks/a0-connector.md`

### Codex

- Main binary: `/Users/home/.nvm/versions/node/v22.19.0/bin/codex`
- Wrapper for A0/Agent Zero: `/Users/home/.local/bin/codex`
- Codex auth: `/Users/home/.codex/auth.json`

## Current known-good smoke tests

### Hermes → Codex

A temp git repo smoke test returned:

```text
CODEX_READY
```

### Agent Zero → A0 → host Mac

Agent Zero used `code_execution_remote` through A0 and returned:

```text
/Users/home
/Users/home/.local/bin/codex
codex-cli 0.125.0
```

### Agent Zero HTTP

```text
HTTP 200
```

## Expansion docs added

- `runbooks/agent-zero.md` now contains the exact reproducible Agent Zero setup path: Colima/Docker install, non-interactive container run, OpenRouter key wiring, HTTP/UI verification, and A0 handoff.
- `runbooks/a0-connector.md` now contains the exact A0 setup path: installer, tmux session, Read&Write/code-exec toggles, launchd persistence, Codex wrapper, and remote Codex verification.
- `docs/cloud-computer-options.md` documents the conditional Orgo AI/managed-cloud-computer decision for VPS and commercial deployments.
- `docs/steipete-tool-intake.md` documents prioritized Peter/steipete tools for future Super Agent integration.

## Optional future tool candidates

Tier 1 candidates from Peter/steipete intake:

- Peekaboo
- macos-automator-mcp
- gogcli
- wacli
- claude-code-mcp
- agent-rules
- mcporter

Optional premium runtime candidate:

- Orgo AI or equivalent managed cloud computer, only for VPS/customer deployments requiring isolated visual desktops or persistent GUI browser workspaces.
