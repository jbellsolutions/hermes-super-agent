# Changelog

All notable changes to agent-os.

## [0.1.0] — 2026-04-29

### Added
- Initial scaffold of the unified agent-os repo.
- Architecture: Hermes (orchestrator) + specialist runtimes (OpenClaw, browser-use, Aider, Codex, Claude Code subagents, Anthropic Computer Use, Claude Managed Agents, E2B, Exa, LiveKit, Terminal) + agi-1 (quality) + Vault + Manifest + Upgrader + Channels + Webapp + Dashboard.
- Vendored upstream OSS as git submodules: hermes-agent, openclaw, nemoclaw (parked), browser-use, aider, awesome-hermes-agent, agi-1.
- Auto-updater daemon scaffolded with 10 nightly streams.
- Single-state accessibility layer: Slack + Telegram + web text + web voice → same Hermes instance.
- Self-healing state machine, self-learning autoresearch loop, self-growing upgrader, self-skills via Hermes' native skill saving + agi-1 promotion.
- `/explain` skill backed by manifest MCP server for system introspection.
- Deploy templates: Railway / Docker Compose / Fly.io.
- CI workflow with smoke + lint + type + unit gates.

### Notes
- NemoClaw integration wired but disabled — flip `UPGRADER_ENABLE_NEMOCLAW=true` once NVIDIA marks it GA.
- 14 old framework repos remain live per Justin's call. Revisit archive question after one vertical app onboards onto agent-os end-to-end.

## Super Agent conversion

- Rebased `hermes-super-agent` onto `jbellsolutions/agent-os` as the actual repo foundation.
- Added Super Agent identity, operating model, and runtime docs.
- Added Agent Zero + A0 as a documented runtime layer.
- Preserved prior Hermes/Codex/Agent Zero/A0 setup documentation under `docs/local-stack/`.
- Added `super-agent` CLI alias while keeping `agent-os` compatibility.

## Setup backlog

- Added `docs/setup-backlog.md` to track remaining tool, skill, runtime, and integration setup.

## Safe daily updates

- Added `docs/update-policy.md` with the rule that new tools must update the repo.
- Changed nightly upgrades to open a reviewable PR only after updater streams, Ruff, and smoke/unit tests pass.
- Kept the upgrade posture conservative: stable and consistent beats newest.

## Agent Zero reproduction + expansion intake

- Expanded `runbooks/agent-zero.md` with the exact Colima/Docker, Agent Zero, OpenRouter, health-check, and A0 handoff steps that made the local stack work.
- Expanded `runbooks/a0-connector.md` with the exact A0 install, tmux, launchd, Read&Write/code-exec, Codex wrapper, and remote Codex verification steps.
- Added `docs/cloud-computer-options.md` with the Orgo AI/managed-cloud-computer recommendation: optional premium runtime, not a baseline dependency.
- Added `docs/steipete-tool-intake.md` with prioritized intake for Peter/steipete tools.
- Updated README, architecture, inventory, roadmap, and setup backlog to point future Hermes agents at the new runbooks and decision docs.

## Commercial setup and portfolio architecture

- Added `docs/commercial-packaging.md` with Operator / Pro Operator / Enterprise tier definitions.
- Added `docs/portfolio-agent-architecture.md` with the recommended hub-and-spoke model: one primary Hermes Super Agent plus isolated specialist business/customer agents.
- Added `runbooks/deployment-access.md` for safe read-only Railway and DigitalOcean inventory before any infrastructure changes.
- Updated `LAUNCH.md`, `.env.example`, `scripts/launch.py`, and `.claude/skills/agent-os/SKILL.md` so dropped-link setup asks for business context, tier, first workflows, approval rules, deployment target, and only the relevant keys.
- Documented COO Agent, Agent Company, and Paperclip as related repos to inventory and fold into the specialist-agent/productization path.

## Railway connection and specialist-agent operations

- Connected Railway CLI as `jbellsolutions` and captured a redacted read-only inventory in `docs/deployments-inventory.md`.
- Installed DigitalOcean CLI (`doctl`) and documented DigitalOcean auth as pending token/`doctl auth init`.
- Added `docs/specialist-agent-operations.md` describing how one primary Hermes chat can observe, rebuke/nudge, assign work to, and eventually control isolated specialist agents.

## DigitalOcean inventory, Paperclip roadmap, and Symphony intake

- Authenticated DigitalOcean using a token stored outside the repo and captured a redacted read-only inventory in `docs/deployments-inventory.md`.
- Added `docs/portfolio-roadmap.md` with the recommended sequence: primary Hermes as hub, business-only COO specialist later, Paperclip as a pluggable dashboard/control-plane candidate, and read-only infrastructure mapping first.
- Added `docs/symphony-intake.md` evaluating OpenAI Symphony as a coding-agent orchestration pattern, not a default dependency yet.
- Added initial `vault/projects/` maps for `paperclip-ops`, `agentstack-hermes`, and `coo-platform`.

## Deployment health pilot and builder swarm harness

- Narrowed the first pilot to deployment health mapping, Railway `coo-platform`, Railway `agentstack-hermes`, and Paperclip inspection; `single-brain` and `cold-email-agent` are explicitly skipped for now.
- Added `docs/deployment-health-specialist.md` for the first observe/report specialist-agent pilot.
- Added `docs/builder-swarm-harness.md` and `templates/WORKFLOW.md` to capture Symphony-style coding-agent harness engineering without adopting Symphony as a mandatory runtime.
- Updated project maps with read-only findings: `coo-platform` health check is live, `agentstack-hermes` is serving Hermes API and Paperclip UI, and `paperclip-ops` SSH is blocked by missing accepted key.

## Single Brain COO rebuild and Cursor SDK intake

- Added `docs/coo-single-brain-rebuild.md` to define the rebuild path for the business-only Single Brain COO: Justin keeps Primary Hermes as the everything-builder/hub, while the COO becomes the operational cofounder controlling Paperclip company teams later.
- Added `vault/projects/single-brain.md` after read-only DigitalOcean inspection; the droplet exists and is active, but SSH/public HTTP access is currently blocked.
- Deepened `vault/projects/agentstack-hermes.md` with Paperclip health/API inventory, discovered endpoint families, and private/authenticated-board behavior.
- Added `docs/cursor-sdk-intake.md` and `docs/builder-tool-architecture.md` to position Cursor SDK as an optional builder-swarm backend behind the same Symphony-style `WORKFLOW.md` harness, alongside Codex, Claude Code, OpenClaw, Hermes subagents, Composio/MCP connectors, and browser/computer tools.
