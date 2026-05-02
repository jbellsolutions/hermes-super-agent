# Super Agent Runtime: Codex + Agent Zero + A0

This repo started from `jbellsolutions/agent-os` and adds Justin's local Super Agent runtime.

## Runtime inventory

### Hermes

- Role: primary operator / mission controller.
- Interface: Telegram, CLI, scheduled jobs, tools, memory, skills.
- Rule: untagged work routes to Hermes first.

### Codex CLI

- Role: code execution engine for repos.
- Local executable: `/Users/home/.nvm/versions/node/v22.19.0/bin/codex`
- Host wrapper: `/Users/home/.local/bin/codex`
- Verified version: `codex-cli 0.125.0`
- Smoke test previously returned: `CODEX_READY`

### Agent Zero

- Role: browser-visible autonomous agent UI.
- URL: `http://127.0.0.1:5080`
- Docker container: `agent-zero`
- Data directory: `/Users/home/agent-zero/agent-zero/usr`
- Binding: localhost only.

### A0 connector

- Role: bridge from Agent Zero to Mac host tools/files.
- Version previously verified: `a0 1.5`
- tmux session: `a0`
- LaunchAgent: `com.justin.a0-connector`
- Local host path: `/Users/home`
- Remote Agent Zero path: `/a0/usr/workdir`
- Permissions: Read/Write enabled; code execution enabled.

### Docker/Colima

- Role: local container runtime.
- Colima is preferred over Docker Desktop because it is lighter, terminal-controllable, and avoids Docker Desktop account/licensing friction.

## Health checks

Use:

```bash
./scripts/health-check-local-stack.sh
```

Typical checks:

- `hermes --version`
- `codex --version`
- `a0 --version`
- `docker ps --filter name=agent-zero`
- `curl -I http://127.0.0.1:5080`
- `launchctl print gui/$(id -u)/com.justin.a0-connector`
- `tmux has-session -t a0`
- `df -h /`

## Start/stop quick reference

```bash
colima start
docker start agent-zero
docker stop agent-zero
docker restart agent-zero
docker ps --filter name=agent-zero
tmux attach -t a0
```
