# Hermes Super Agent

A living documentation repo for Justin's local super-agent stack: **Hermes + Agent Zero + A0 Connector + Codex + Docker/Colima**.

This repo exists to track what is installed, what works, what breaks, operational runbooks, experiment notes, and the evolving gameplan as we build toward a highly capable local AI operating environment.

## Current stack

- **Hermes Agent**: Telegram-accessible command center/orchestrator.
- **OpenAI Codex CLI**: coding agent for repo work, reviews, and refactors.
- **Agent Zero**: local browser UI autonomous agent running in Docker.
- **A0 CLI Connector**: bridge from Agent Zero to the host Mac filesystem/shell.
- **Colima + Docker**: local container runtime.
- **OpenRouter**: model provider used by Agent Zero.

## Key local URLs and paths

- Agent Zero UI: <http://127.0.0.1:5080>
- Agent Zero container: `agent-zero`
- Agent Zero data: `/Users/home/agent-zero/agent-zero/usr`
- A0 connector tmux session: `a0`
- A0 connector launchd label: `com.justin.a0-connector`
- Codex wrapper for A0/Agent Zero: `/Users/home/.local/bin/codex`
- This repo: `/Users/home/Desktop/Hermes Super Agent`

## Repository structure

```text
.
├── README.md
├── docs/
│   ├── inventory.md
│   ├── setup-log.md
│   ├── architecture.md
│   └── roadmap.md
├── runbooks/
│   ├── agent-zero.md
│   ├── a0-connector.md
│   ├── codex.md
│   ├── hermes.md
│   └── disk-cleanup.md
├── decisions/
│   └── 0001-local-agent-stack.md
├── templates/
│   ├── experiment-log.md
│   ├── project-registry.md
│   └── agent-task-brief.md
├── scripts/
│   └── health-check.sh
└── logs/
    └── .gitkeep
```

## Operating model

1. **Hermes is mission control** from Telegram.
2. **Codex handles serious coding tasks** inside git repos/worktrees.
3. **Agent Zero handles visual/autonomous workflows** and experiments.
4. **A0 Connector lets Agent Zero operate on the host Mac**.
5. **Docker/Colima runs local services** like Agent Zero and future infrastructure.


## Agent OS imported

We imported Builder Methods Agent OS as a spec/standards workflow layer. See:

- `docs/agent-os-integration.md`
- `.claude/commands/agent-os/`
- `agent-os/standards/`
- `third_party/agent-os/`

Use Agent OS patterns to discover standards, inject standards, shape specs, and plan products before sending implementation work to Codex or Agent Zero.

## Maintenance habit

Whenever we change the setup, add a tool, discover a failure mode, or find a strong workflow:

1. Update the relevant runbook.
2. Add a dated entry to `docs/setup-log.md`.
3. Add any architectural implication to `docs/architecture.md`.
4. Commit the changes.

## Quick health check

```bash
./scripts/health-check.sh
```
