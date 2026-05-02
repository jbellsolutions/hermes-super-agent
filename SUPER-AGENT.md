# Super Agent Operating Model

Super Agent is a practical distribution of Agent OS for Justin's local autonomous-agent stack.

## Core layers

- **Agent OS**: base repo, manifest, vault, quality flywheel, channel model, upgrade scaffolding.
- **Hermes**: main command center and Telegram interface. Use Hermes for orchestration, scheduling, tool calling, memory, and deciding which runtime should do the work.
- **Codex CLI**: coding runtime for implementation, tests, refactors, repo tasks, and smoke checks.
- **Agent Zero**: browser-visible autonomous UI and experimental visual agent layer.
- **A0 connector**: bridge from Agent Zero to the Mac host filesystem/commands.
- **Docker/Colima**: local service runtime for Agent Zero and future services.

## Current local installation

- Agent Zero UI: `http://127.0.0.1:5080`
- Agent Zero container: `agent-zero`
- Agent Zero data: `/Users/home/agent-zero/agent-zero/usr`
- A0 tmux session: `a0`
- A0 launchd label: `com.justin.a0-connector`
- A0 startup script: `/Users/home/bin/start-a0-connector.sh`
- Codex wrapper visible to A0: `/Users/home/.local/bin/codex`

Secrets and auth files are intentionally not copied into this repo. If a command or doc references credentials, record the location and write `[REDACTED]`, never the value.

## Routing rule

1. Use **Hermes** by default.
2. Use **Codex** for code changes and tests.
3. Use **Agent Zero** when visual/browser UI or autonomous interactive work is useful.
4. Use **A0** when Agent Zero needs host filesystem/command access.
5. Use **Agent OS vault/docs** as the durable record of what worked, what broke, and what changed.

## Documentation rule

Every stack change should update at least one of:

- `CHANGELOG.md`
- `docs/local-stack/`
- `docs/super-agent-runtime.md`
- `vault/decisions/`
- `vault/incidents/`
- `vault/upgrades/`
