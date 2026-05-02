# Execution Plan

Stages 1–11+ for going from approved-plan to production. Each stage has an acceptance check; don't move on without it.

## Stage 1 — Repo + skeleton + submodules ✅ (this commit)

- `gh repo create jbellsolutions/agent-os --private`
- 7 git submodules: hermes-agent, openclaw, nemoclaw (parked), browser-use, aider, awesome-hermes-agent, agi-1
- Skeleton: `packages/{orchestrator,runtimes,manifest,quality,upgrader,channels,observability,webapp,dashboard}` with stub modules
- Top-level docs: README, ARCHITECTURE, ETHOS, ECOSYSTEM-PLAYBOOK, MIGRATION-MAP, CLAUDE.md
- `.claude/` skill stubs registered
- CI workflow (lint + type + smoke + unit)
- Deploy templates: Railway / Docker / Fly

**Acceptance**: `uv sync && pnpm install` both succeed; `python -c "import agent_os.orchestrator, agent_os.runtimes, agent_os.manifest, agent_os.quality, agent_os.upgrader, agent_os.channels"` succeeds; `gh repo view jbellsolutions/agent-os` shows the repo.

## Stage 2 — Boot Hermes as the orchestrator

- Convert `agent-core/identities/coo-template.json` → `packages/orchestrator/config/identities/coo.yaml`.
- Implement `packages/orchestrator/adapters/vault_memory.py` (Hermes ↔ vault).
- `packages/orchestrator/boot.py` starts Hermes pointed at our config + Slack.

**Acceptance**: Hermes boots, joins Slack, responds, persists conversation to `vault/conversations/`. Default behavior: Hermes handles all work itself (no specialists wired).

## Stage 3 — Wire OpenClaw as first specialist runtime

- `packages/runtimes/openclaw/config/` — tool allowlists, shell scope, browser profile.
- `packages/runtimes/openclaw/invoke.py` — `openclaw.invoke(job) → result`.
- `packages/runtimes/openclaw/outputs.py` — round-trips to `vault/runs/`.
- First router rule in `job_router.py`: `autonomous-grind | shell | browser-heavy` → OpenClaw.

**Acceptance**: Hermes receives a `browser-heavy`-tagged job, router picks OpenClaw, OpenClaw executes, output in `vault/runs/`. Untagged job stays in Hermes.

## Stage 3b — Wire other specialist runtimes

`browser_use`, `claude_subagents`, `codex_cli`, `aider`, `claude_managed`, `computer_use`, `e2b`, `exa`, `livekit`, `terminal`. Each ≤100 lines, each with a router rule.

**Acceptance**: each runtime invokable in isolation; router picks correctly per tags.

## Stage 4 — Wire AGI-1 as Quality

- `packages/quality/invocations/{audit,council,research}.py` — thin wrappers calling agi-1 skills.
- Register agi-1 skills with Hermes' skill index so Hermes can invoke `/agi-audit` directly.

**Acceptance**: nightly Hermes job runs `/agi-audit` against day's vault outputs and writes a score file to `vault/daily/<date>.md`.

## Stage 5 — Build the auto-update daemon

- `packages/upgrader/streams/{hermes,openclaw,browser_use,aider,codex,agi1,awesome_hermes,nemoclaw,mcp_registry,vendor_health}.py` — 10 streams.
- Smoke fixtures in `packages/upgrader/smoke/`.
- Cron at 02:00 (env-configurable).
- Dashboard rollback button.

**Acceptance**: simulate upstream commit → upgrader picks up → smoke passes → promote → log to `vault/upgrades/`. Simulate bad commit → quarantine branch + Slack alert.

## Stage 6 — Manifest layer

- `packages/manifest/{schema,aggregator,mcp_server,explain}.py`.
- Drop `manifest.yaml` files into existing vertical app repos so the graph has nodes to walk.

**Acceptance**: `/explain "what wrote my morning brief?"` returns a real walked answer.

## Stage 7 — Slack + Telegram with single-state guarantee

- Configure Hermes' Slack adapter with vault file-upload handler.
- Configure Hermes' Telegram adapter.
- Verify single-state: drop value via Slack, retrieve via Telegram, same conversation log.

**Acceptance**: send "remember 42" via Slack, ask via Telegram, returns 42 with same context.

## Stage 8 — Web app: streaming text chat + file upload

- `packages/webapp/` Next.js, WebSocket bridge to Hermes.
- Streaming chat UI, drag-drop file upload.
- Same conversation thread keyed to user.

**Acceptance**: streaming works, file context cross-channel works.

## Stage 9 — Voice: LiveKit + Realtime API

- LiveKit server (self-host or LiveKit Cloud).
- Voice agent worker via LiveKit Agents.
- OpenAI Realtime API as default voice model; Gemini Realtime configurable.

**Acceptance**: voice round-trip <2s on clean connection. Single-state preserved.

## Stage 10 — One-command deploy

- Railway template + Docker Compose + Fly.io variant.
- README has copy-paste env blocks per channel.

**Acceptance**: fresh checkout → one command → full stack running.

## Stage 11+ — Vertical apps onboard one at a time

Each gets a `manifest.yaml`, points work at agent-os entry points, joins the graph. No big-bang migration.
