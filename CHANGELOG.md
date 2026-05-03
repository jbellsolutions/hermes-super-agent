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

## Vault sync and routing intelligence

- Added `docs/vault-sync-contract.md` making Obsidian + Notion sync mandatory for conversations, actions, decisions, health reports, and agent activity.
- Added `docs/routing-intelligence-contract.md` defining when to use GPT-5.5, Opus 4.7, DeepSeek, Cursor SDK, Codex, Claude Code, Hermes subagents, browser/computer backends, and scoped tool bundles.
- Updated the Single Brain COO plan with Justin's decisions: merge COO Agent + Single Brain sources, separate COO Hermes profile/VPS, own Telegram chat/bot if needed, initial Paperclip companies, and 7-day smoke test before retiring legacy `coo-platform`.

## Hermes-first install, bidirectional brain, and dual frontier routing

- Added `docs/hermes-first-install-walkthrough.md` so a fresh computer/customer/Zions install starts by installing and verifying Hermes Agent, then configures Super Agent tools, shared brain sync, channels, tier, and smoke tests.
- Updated `LAUNCH.md` and README drop-link prompts so Claude Code/Codex install Hermes first when missing instead of assuming the target machine already has Hermes.
- Strengthened `docs/vault-sync-contract.md` from write-only logging to bidirectional shared-context retrieval: agents must write to and pull from Obsidian/Notion before answering cross-agent, cross-business, contact, offer, project, or deployment questions.
- Updated routing/tool architecture so GPT-5.5 and Claude Opus 4.6/4.7 work together on architecture, debugging, security, auth, unit tests, and high-stakes deployment coding; Claude remains especially strong for content, design, and brand voice.
- Clarified Cursor SDK as the preferred coding-team/harness runtime candidate, with Symphony used as an optional harness reference rather than a mandatory dependency when `WORKFLOW.md` plus Cursor SDK is sufficient.

## Private bootstrap overlay and secret-broker product pattern

- Added `docs/private-bootstrap-overlay.md` to document the public/product-safe pattern for a separate private encrypted bootstrap repo.
- Documented how internal owner agents can inherit shared encrypted env/tool/skill access while keeping unique per-agent credentials such as Telegram bot tokens separate.
- Documented the commercial version: company-owned secret broker, role-scoped access, audit logs, and no raw master credentials exposed to ordinary role agents.
- Extended the private overlay guidance for remote/VPS agents: controller-push over SSH, per-machine age recipients, deploy keys/temporary PATs, and commercial secret-manager bootstrap.

## Zions install boot-command clarification

- Clarified that `uv run agent-os boot` is a Stage 2 scaffold diagnostic, not the live Hermes launcher yet.
- Updated `scripts/launch.py`, `LAUNCH.md`, README, and `docs/hermes-first-install-walkthrough.md` to direct fresh installs to run `hermes doctor` and `hermes` for the actual Hermes CLI.
- Updated `src/agent_os/orchestrator/boot.py` so future `agent-os boot` output says `scaffold_not_error` and returns the correct next commands instead of looking like a failed install.

## Launch wizard installs Hermes first

- Added a Step 0 Hermes Agent preflight to `scripts/launch.py`: if `hermes` is missing, the wizard runs the official Nous Research installer before asking Super Agent onboarding questions.
- Added `--skip-hermes-install` for operators who intentionally want to install Hermes manually first.
- Added unit coverage for both paths: missing-Hermes installer invocation and installed-Hermes skip behavior.
- Updated README, `LAUNCH.md`, `docs/hermes-first-install-walkthrough.md`, and `scripts/bootstrap.sh` so the wizard no longer looks like it completed while leaving Hermes absent.
