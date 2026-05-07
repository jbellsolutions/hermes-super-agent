# Super Agent

> **Agent OS + Hermes + Codex + Agent Zero.**
>
> Super Agent is Justin's Agent OS distribution: the `jbellsolutions/agent-os` foundation plus the local stack we have running now — Hermes as command center, Codex as the coding engine, Agent Zero as the visual/autonomous UI, and A0 as the host bridge.
>
> Upstream base: [`jbellsolutions/agent-os`](https://github.com/jbellsolutions/agent-os). This repo is the Super Agent fork/version where we wire in Codex, Agent Zero, A0, local runbooks, and experiments.

## What changed from Agent OS

- Agent OS is now the **base operating system** of this repo, not a vendored side folder.
- Super Agent adds the local Hermes/Codex/Agent Zero/A0 operating model.
- The previous setup docs were preserved under [`docs/local-stack/`](./docs/local-stack/).
- Codex stays a first-class coding runtime.
- Agent Zero + A0 are added as a first-class visual/autonomous runtime layer.
- Local health checks and runbooks remain part of the repo so we document what works as we build.

---

> **One agent. One state. Every channel. Daily-evolving.**
>
> Hermes drives. Agent Zero + A0 provide a visual/autonomous host bridge when needed. OpenClaw + browser-use + Aider + Codex + Claude Code + Anthropic Computer Use + Claude Managed Agents + LiveKit + E2B + Exa are its tool belt. AGI-1 is the quality flywheel. The vault is the single source of truth. The upgrader pulls every dependency upstream every night. Drop a file in Slack, voice-chat the answer on the web — same agent, same memory.

[**Read the founding story →**](./STORY.md) — *how 14 broken frameworks became one that actually works.*

---

## Drop the link, get rolling

Three paths. Pick one. **You don't need to read the rest of this README to launch.**

### Path A — Hermes-first walkthrough via Claude Code/Codex (recommended)

Drop this in any Claude Code or Codex session:

> *"Set up a Hermes Super Agent for me. Repo: https://github.com/jbellsolutions/hermes-super-agent. Start by checking whether Hermes Agent is installed. If Hermes is missing, install it from the official Hermes installer. Then interview me in plain English, ask only for the keys needed for my chosen tier, connect the shared Obsidian/Notion brain if available, and verify everything before you say it is ready."*

Claude Code/Codex will read the setup instructions, [`docs/hermes-first-install-walkthrough.md`](./docs/hermes-first-install-walkthrough.md), and the [`agent-os` skill](./.claude/skills/agent-os/SKILL.md), detect whether Hermes exists on the machine, install/configure it if needed, then walk through every Super Agent step in plain English — business context, tier, keys, channels, shared brain, deploy target, tools, and verification. This is the preferred first test path for Zions' computer and the commercial setup experience.

### Path B — One-command wizard

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
./scripts/launch.py
```

Conversational Python wizard. It starts with a Hermes Agent preflight: if `hermes` is missing, it installs Hermes from the official Nous Research installer before asking Super Agent questions. Then it collects the primary Hermes provider/key — OpenRouter by default — optional Telegram bot token + allowed user ID, business context, tier, approval rules, and deploy target. It writes both the Super Agent `.env` and Hermes' own env/config, runs `uv sync` + `pnpm install`, runs smoke tests, builds the manifest graph, and hands you a summary.

### Path C — Self-driving setup (Hermes drives)

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
./scripts/launch.py --minimal      # asks for provider key, operator, and Telegram quick access
hermes doctor
hermes
```

Then tell Hermes: *"Set yourself up. I want Slack + Telegram + web voice. Keys are in 1Password under 'agent-os/*'. Deploy to Railway when ready."* Hermes uses its own tools and skills to finish configuration. `uv run agent-os boot` is currently a Stage 2 scaffold diagnostic, not the live Hermes launcher. *(Full self-setup loop lights up after stages 3–10 of `docs/EXECUTION-PLAN.md`.)*

[**Full launch guide →**](./LAUNCH.md)

---

## What you're getting

| | |
|---|---|
| **Persistent orchestrator** | [Hermes](https://github.com/NousResearch/hermes-agent) — 64K★ MIT-licensed, persistent memory across sessions, native skill saving, multi-platform Slack/Telegram/Discord/WhatsApp/CLI, bring-any-model. |
| **Autonomous execution** | [OpenClaw](https://github.com/openclaw/openclaw) — 302K★, the fastest-growing OSS project ever. Shell, file, browser grind. |
| **Multi-agent deliverables + agent-builder** | [OpenSwarm](https://github.com/VRSEN/OpenSwarm) — vendored multi-agent deliverable production (slides, decks, research, charts, docs, images, video). Plus the **agent-builder agent**: tell Hermes "build me an SEO swarm" and the runtime forks the vendor, customizes via `claude_code` or `manual` customizer, validates, and registers a new fleet member with auto-routing. Per-swarm folder/port/.env/manifest. See [`vault/decisions/openswarm-runtime-adoption.md`](./vault/decisions/openswarm-runtime-adoption.md). |
| **Structured browser** | [browser-use](https://github.com/browser-use/browser-use) — 50K★ AI-agent-grade browser automation. |
| **Coding (interactive)** | Claude Code subagents — direct, in-repo. |
| **Coding (background)** | OpenAI Codex CLI + [Aider](https://github.com/Aider-AI/aider) — multi-provider hedge so a single outage doesn't stop the press. |
| **Visual autonomous workspace** | [Agent Zero](https://www.agent-zero.ai/) + A0 Connector — Dockerized web UI with host Mac bridge and Codex access. See [`runbooks/agent-zero.md`](./runbooks/agent-zero.md) and [`runbooks/a0-connector.md`](./runbooks/a0-connector.md). |
| **Raw desktop** | Anthropic Computer Use SDK. |
| **Long-running cloud** | Anthropic Claude Managed Agents. |
| **Sandboxed code** | E2B — clean VM per run. |
| **Search** | Exa neural search for "find me 10 articles about X" without spinning up a browser. |
| **Voice + realtime** | LiveKit + OpenAI Realtime API or Gemini Realtime API. |
| **Quality flywheel** | Your own [agi-1](https://github.com/jbellsolutions/agi-1) — vendored, auto-updated nightly to itself. `/agi-audit`, `/agi-council`, `/agi-research`. |
| **Observability** | Self-hosted Langfuse + optional NVIDIA NeMo Agent Toolkit — free, no surprise costs. |
| **Memory** | Markdown vault → Supabase mirror. Single-state across every channel. |
| **Introspection** | Manifest layer + MCP server + `/explain` skill — finally answers "how do you all tie together?" |
| **Security wrapper** | NemoClaw vendored and parked until NVIDIA marks GA — flip the env var the day they do. |
| **Optional cloud computer** | Orgo AI or equivalent managed machine only when a VPS/customer deployment needs an isolated visible desktop. See [`docs/cloud-computer-options.md`](./docs/cloud-computer-options.md). |

## Commercial packaging

- **Operator** — default. Hermes + Codex + core tools + gateway + vault + safe updates. Best for one internal operator/business.
- **Pro Operator** — Operator plus Agent Zero/A0 and the default recommended Tier 1 tool pack when prerequisites pass: Peekaboo, macos-automator-mcp, gogcli, wacli, claude-code-mcp, agent-rules, mcporter.
- **Enterprise** — isolated customer/project deployments, Railway/DigitalOcean/VPS discovery, cost caps, approval gates, optional Orgo/managed cloud computer.

Orgo is never a default dependency. It is a premium Enterprise option when a customer/workspace needs an isolated visible cloud computer.

See [`docs/commercial-packaging.md`](./docs/commercial-packaging.md).

The differentiator isn't adopting Hermes + OpenClaw — anyone can do that. The differentiator is running them tied together with **daily auto-updates** and a **quality flywheel** and a **single-state accessibility layer** that makes Slack, Telegram, web text, and web voice feel like one agent. See [STORY.md](./STORY.md) for the why.

---

## The four "self-" pillars

| Pillar | Mechanism |
|---|---|
| **Self-healing** | Hermes heartbeat detects (heartbeats, validators, cron, API health, cost). Signature-match against `vault/genome/incidents.yaml`. Apply genome fix or 3-agent diagnostic council. Verify. Auto-promote recurring fixes. |
| **Self-learning** | Every run writes binary assertions to `vault/runs/`. Nightly rollup detects plateau/regression. `/agi-research` evolves prompts via 5-variation tournament; promotes winner if it beats incumbent by ≥5pp. |
| **Self-growing** | Upgrader pulls Hermes / OpenClaw / browser-use / Aider / Codex / agi-1 / awesome-hermes-agent nightly. New capabilities appear automatically. New MCP servers auto-discovered. |
| **Self-skills** | Hermes natively saves successful approaches as reusable skills. agi-1 promotes high-confidence skills cross-project via the genome. |

Concrete state machines for each in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Not vibes.

---

## Repo map

```
src/agent_os/
├── orchestrator/    # Hermes wiring (boot, identities, vault-memory adapter, job router)
├── runtimes/        # specialist tool belt — Hermes routes here per job tags
│   ├── openclaw/    │   ├── openswarm/
│   ├── browser_use/ │   ├── agent_zero/
│   ├── computer_use/│   ├── claude_subagents/
│   ├── codex_cli/   │   ├── aider/
│   ├── claude_managed/ ├── e2b/
│   ├── exa/         │   ├── livekit/
│   └── terminal/
├── manifest/        # introspection — graph aggregator, MCP server, /explain backend
├── quality/         # agi-1 invocations — audit, council, autoresearch
├── upgrader/        # nightly auto-update daemon (10 streams)
├── channels/        # slack / telegram / web / voice — single-state guarantee
└── observability/   # Langfuse + optional NVIDIA NeMo Agent Toolkit

vendor/              # auto-updated upstream OSS — DO NOT EDIT
├── hermes-agent/    │   ├── openclaw/         │   ├── openswarm/
├── browser-use/     │   ├── aider/            │   ├── awesome-hermes-agent/
├── agi-1/           │   └── nemoclaw/  (parked)

vault/               # markdown source of truth → Supabase mirror
├── conversations/   # cross-channel logs (single-state)
├── runs/            # structured run artifacts
├── incidents/       # self-healing record
├── upgrades/        # nightly upgrade log
├── skills/          # active + community-staged + templates
├── genome/          # cross-project promoted patterns
└── graph/           # generated by manifest aggregator

packages/webapp/     # Next.js — streaming chat + voice mode
packages/dashboard/  # Next.js — operator UI

examples/            # vertical apps that consume agent-os
├── sdr-fleet/
├── content-engine/
└── coo-control-room/

.claude/skills/      # /agent-os, /explain, /route, /heal, /agi-audit, /agi-research, /manifest
.claude/mcp.json     # registers the manifest MCP server locally

deploy/              # Railway / Docker Compose / Fly.io templates
```

---

## Daily life

Three things happen automatically every day, no human in the loop:

1. **02:00** — the upgrader runs (11 streams). Pulls Hermes / OpenClaw / OpenSwarm / browser-use / Aider / Codex / agi-1 / awesome-hermes-agent. Smokes each (OpenSwarm's smoke replays each registered swarm's customization against the fresh vendor — catches "upstream change broke our build"). Promotes the green ones. Quarantines the red ones with a Slack alert. Logs to `vault/upgrades/<date>.yaml`.
2. **02:30** — `/agi-audit` runs against the day's outputs. Scores `vault/runs/`. Flags regressions. Writes `vault/daily/<date>.md`.
3. **Every 5 minutes** — the self-healing loop ticks. Polls heartbeats, validators, cron, API health, cost guardrails. Auto-fixes known patterns; spawns a council for unknown ones.

You wake up. The system has improved itself a little. Yesterday's fixes are in the genome. Costs are under budget or you got a Slack alert at 80%. Repeat.

---

## Status — verified at scaffold time

```
✓ uv sync                         # all packages install cleanly
✓ uv run pytest -q                # 128 passed (OpenSwarm runtime + builder + ops + Slack)
✓ uv run agent-os route --tags ...# router returns correct runtime per tag
✓ uv run agent-os manifest        # 20 nodes, 57 edges built
✓ git submodule status            # 8 submodules pinned (added vendor/openswarm)
```

What's stubbed (per [`docs/EXECUTION-PLAN.md`](./docs/EXECUTION-PLAN.md)):

- **Stage 2** — real Hermes boot
- **Stage 3** — real OpenClaw `invoke()`, then the other 10 specialists
- **Stage 4** — real AGI-1 invocations
- **Stage 5** — real upgrader smoke checks
- **Stage 6** — real manifest MCP server
- **Stages 7–9** — Slack/Telegram/web/voice channel wiring
- **Stage 10** — deploy templates verified end-to-end
- **Stage 11+** — vertical-app onboarding

The 14 old framework repos remain live and untouched per Justin's call. They were the pattern that this repo exists to break.

---

## OpenSwarm fleet — the agent-builder agent

[OpenSwarm](https://github.com/VRSEN/OpenSwarm) is vendored at `vendor/openswarm` and wired in as the `runtime.openswarm` specialist. It's the only runtime that owns a *fleet* — Hermes can fork the vendor into N business-purpose-specific swarms (SEO, sales, ops, …), each with its own folder, port, `.env`, and manifest under `~/.agent-os/swarms/<name>/`. The fleet's registry, port allocator, and run logs all live under `~/.agent-os/swarms/registry.yaml` and `vault/runs/openswarm/`.

What you actually type:

```bash
# Tag-based routing — Hermes auto-selects the runtime
uv run agent-os route --tags build-swarm           # → openswarm
uv run agent-os route --tags multi-deliverable     # → openswarm
uv run agent-os route --tags slides+research+docs  # → openswarm

# Direct invocation (Slack/Telegram/CLI all funnel through this)
invoke({"op": "build", "name": "seo-swarm",
        "description": "SEO research, competitor analysis, blog writing",
        "customizer": "claude_code"})              # forks + customizes + validates
invoke({"op": "run", "swarm": "seo-swarm", "prompt": "Write 3 BoFu posts on AI agents"})
invoke({"op": "list"})                              # show fleet
invoke({"op": "pipeline", "steps": [...]})          # cross-swarm sequential
invoke({"op": "fan_out", "swarm": "default",
        "prompts": [...]})                          # parallel variants

# Slack slash commands (after gateway wiring)
/build-swarm seo-swarm -- SEO research and blog writing
/list-swarms
```

15 invoke ops total: `run`, `list`, `status`, `start`, `stop`, `restart`, `destroy`, `cleanup`, `cost`, `hibernate`, `snapshot`, `pipeline`, `fan_out`, `build`, `upgrade`. Three customizers (`noop` / `manual` / `claude_code`), three validators (`noop` / `health` / `smoke`). Atomic rollback on every failure path. Per-swarm budget guard with soft-warn at 80% and hard-block at 100%. Dashboard tile in `packages/dashboard/app/page.tsx` reads `vault/graph/openswarm.json`.

Full design rationale, customizer/validator contracts, multi-instance correctness story, and verification checklist: [`vault/decisions/openswarm-runtime-adoption.md`](./vault/decisions/openswarm-runtime-adoption.md).

---

## Tool awareness — every agent knows every tool

Every agent in the stack — primary Hermes, sub-agents, identity-scoped operators (COO / GTM / Head of Ops) — boots with full awareness of every tool and runtime available, including when to use it, when not to, what it costs, what it risks, and which model should drive it. The system surfaces a **tool plan** at task entry so you see "I'll use X with model Y because Z" *before* anything runs.

**Five layers, each readable by the planner and a human:**

1. **Per-tool SKILL.md** under [`vault/skills/active/tools/`](./vault/skills/active/tools/) — one file per runtime (15 today: `hermes_self`, `openclaw`, `openswarm`, `browser_use`, `agent_zero`, `computer_use`, `claude_subagents`, `codex_cli`, `aider`, `claude_managed`, `e2b`, `exa`, `livekit`, `terminal`, `composio`). Frontmatter declares tier / cost_class / risk_class / preferred_models / category; the body explains *when to use*, *when NOT*, *alternatives*, *examples*. Hermes' router scores these on every prompt.
2. **Machine-readable catalog** at [`vault/graph/tool-catalog.yaml`](./vault/graph/tool-catalog.yaml) — auto-generated by `agent-os catalog` from the SKILL.md frontmatter + runtime manifests + identity packs + model registry. Single source of truth for the planner, dashboard, `/explain`, and any future Hermes integration.
3. **Tier classifier** ([`tier_classifier.py`](./src/agent_os/orchestrator/tier_classifier.py)) — heuristic that puts each job into Tier 1 (autonomous + banner), Tier 2 (plan card + 3s grace), or Tier 3 (hard stop, requires `YES`). Rules live in [`config/tiers.yaml`](./src/agent_os/orchestrator/config/tiers.yaml) — tunable without code changes.
4. **Tool planner** ([`tool_planner.py`](./src/agent_os/orchestrator/tool_planner.py)) — scores the catalog against the job, filtered by the agent's identity bundle, returns a `ToolPlan` with primary tool + alternatives + tier + cost/time estimate + model recommendation.
5. **Plan card + override surface** ([`plan_card.py`](./src/agent_os/orchestrator/plan_card.py) + [`plan_overrides.py`](./src/agent_os/orchestrator/adapters/plan_overrides.py)) — formats the plan per tier and parses interception commands.

**Model layer ships in the same plan.** [`config/models.yaml`](./src/agent_os/orchestrator/config/models.yaml) registers seven models — Claude Opus 4.7, Claude Sonnet 4.7, Claude Sonnet 4.6, GPT-5.5, Kimi K2, **DeepSeek v4 Pro**, Gemini 2.5 Pro — with task-class tags, per-Mtok pricing, and dual-frontier review pairs (`gpt-5.5` ↔ `claude-opus-4.7`) for architecture / debug / security / auth / tests / deploy. The model planner ([`model_planner.py`](./src/agent_os/orchestrator/model_planner.py)) is rule-based and deterministic — no LLM call to pick the model.

**Tier-gated UX** matches the principle "transparent when it matters, autonomous when it doesn't":

| Tier | Trigger | Output |
|---|---|---|
| **1** | Read-only, cheap, idempotent (search, status, explain, lookup) | One-line banner: `⚡ using openswarm · claude-opus-4.7` |
| **2** | Mutates / substantive (build, write, generate, send) | 4-line plan card + 3-second grace window for `/cancel` or `/use <tool>` |
| **3** | Destructive / public / expensive (deploy, delete, force-push, send-email, >$1.00) | Hard stop. Requires uppercase `YES` to proceed |

**Override surface** works in any channel (Slack/Telegram/CLI/web):

| Command | Effect |
|---|---|
| `/cancel` | Abort the task |
| `/use <tool>` | Replace primary tool; re-emit plan |
| `/use <tool> <model>` | Replace both |
| `/why` | 5-line rationale (reads SKILL.md + scoring breakdown) |
| `/plan on` / `/plan off` | Per-session: emit cards for all tiers / only ≥2 |
| `/tier 1\|2\|3` | Force this task to a tier (refused for destructive ops on tier 1) |
| `YES` (uppercase) | Confirm a Tier 3 hard stop |

**Identity packs filter the catalog.** Each identity in [`config/identities/`](./src/agent_os/orchestrator/config/identities/) declares `tools_allowed`, `tools_denied`, and `default_tier_ceiling`. A COO can use OpenSwarm for client decks but not Terminal for destructive infra — and a COO asking for a Tier 3 deploy gets `🚫 Blocked: requires primary_hermes approval` instead of an outright refusal. Escalation path is explicit.

**What you actually type:**

```bash
# Show the plan card for a job (no execution)
uv run agent-os plan --tags multi-deliverable --prompt "make me an investor deck"
# → 📋 Plan: make me an investor deck
#   • Tools: openswarm; alts: hermes_self
#   • Model: claude-opus-4.7 (draft) → gpt-5.5 (review)
#   • Tier 2 · ~$0.40 · ~10min · proceeding in 3s · /cancel /use <tool> /why

uv run agent-os plan --tags deploy production --prompt "ship to prod"
# → 🛑 Plan: ship to prod / Tier 3 · destructive · reply YES to proceed

uv run agent-os plan --identity coo --tags deploy production
# → 🚫 Blocked: identity 'coo' has default_tier_ceiling=2; this task is tier 3.

# Inspect / classify / catalog / models
uv run agent-os tier --tags read,explain                           # → tier 1
uv run agent-os tool openswarm                                      # show one SKILL.md
uv run agent-os catalog                                             # rebuild tool-catalog.yaml
uv run agent-os models                                              # list all 7 registered models
```

**Use this layer in another project.** The whole tool-awareness layer is self-contained — ~1100 lines of pure Python, three YAML configs, fifteen markdown skills, no DB, no network calls. To incorporate it into a Hermes-style stack, a different Python orchestrator, or as a standalone library: read [`docs/tool-awareness-handoff.md`](./docs/tool-awareness-handoff.md). It includes the complete file inventory, six integration paths (from "import as a library" up to "full incorporation"), tunable configuration knobs, extension recipes (add a tool, add a model, add an identity), and a verification checklist.

**Reference docs for this layer:**
- [`docs/tool-awareness-handoff.md`](./docs/tool-awareness-handoff.md) — **full handoff doc** for incorporating this layer into another project
- [`docs/tool-cheatsheet.md`](./docs/tool-cheatsheet.md) — auto-generated table of all 15 tools (tier / category / cost / risk / use-when)
- [`vault/decisions/tool-awareness-and-model-routing.md`](./vault/decisions/tool-awareness-and-model-routing.md) — design rationale: why tier-gated transparency, why per-tool SKILL.md, why the model layer ships in the same plan
- [`docs/routing-intelligence-contract.md`](./docs/routing-intelligence-contract.md) — authoritative human-language routing policy (model + backend + tool bundle)

---

## The hard rules

- **Never edit `vendor/`.** It breaks the upgrader. Open an upstream PR or wrap in `src/agent_os/runtimes/`.
- **Never start another framework wrapper.** New ideas go into a runtime adapter, a Hermes skill, or upstream.
- **Single-state guarantee.** Every channel writes through `vault_memory` — no per-channel state.
- **Smoke tests are non-negotiable for the upgrader.** A bad upstream commit silently promoted is the failure mode that takes the system down.
- **Default to Hermes.** Specialist runtimes are exceptions, not defaults.

Full ethos: [`ETHOS.md`](./ETHOS.md). 5-question filter for adopting new tools: [`ECOSYSTEM-PLAYBOOK.md`](./ECOSYSTEM-PLAYBOOK.md). Migration map for the 14 old framework repos: [`MIGRATION-MAP.md`](./MIGRATION-MAP.md).

New operator/runtime intake notes:

- [`docs/commercial-packaging.md`](./docs/commercial-packaging.md) — Operator / Pro Operator / Enterprise packaging and setup contract.
- [`docs/portfolio-agent-architecture.md`](./docs/portfolio-agent-architecture.md) — hub-and-spoke model for one primary Hermes plus specialist business agents.
- [`docs/specialist-agent-operations.md`](./docs/specialist-agent-operations.md) — how specialist agents report to and receive tasks from the primary Hermes agent.
- [`docs/deployments-inventory.md`](./docs/deployments-inventory.md) — redacted Railway/DigitalOcean inventory as discovered.
- [`docs/portfolio-roadmap.md`](./docs/portfolio-roadmap.md) — near-term roadmap for Paperclip, COO specialist, deployment mapping, and specialist-agent sequencing.
- [`docs/symphony-intake.md`](./docs/symphony-intake.md) — OpenAI Symphony/harness-engineering evaluation for coding-agent orchestration.
- [`docs/builder-swarm-harness.md`](./docs/builder-swarm-harness.md) — lightweight Symphony-style builder swarm contract without making Symphony a default dependency.
- [`docs/deployment-health-specialist.md`](./docs/deployment-health-specialist.md) — first specialist-agent pilot: observe/report health, costs, ownership, and broken deployments.
- [`docs/coo-single-brain-rebuild.md`](./docs/coo-single-brain-rebuild.md) — rebuild plan for the business-only Single Brain COO using Super Agent, Paperclip, and the existing COO assets.
- [`docs/cursor-sdk-intake.md`](./docs/cursor-sdk-intake.md) — Cursor TypeScript SDK intake as an optional builder-swarm backend.
- [`docs/builder-tool-architecture.md`](./docs/builder-tool-architecture.md) — coherent tool composition model for Hermes, Paperclip, Symphony, Cursor SDK, Codex, OpenClaw, Composio, and browser/computer tools.
- [`docs/hermes-first-install-walkthrough.md`](./docs/hermes-first-install-walkthrough.md) — Hermes-first setup path for fresh computers, including Zions/customer installs, model setup, shared brain sync, tiered tools, and verification.
- [`docs/private-bootstrap-overlay.md`](./docs/private-bootstrap-overlay.md) — public/product-safe pattern for a separate private encrypted bootstrap repo that can spin up internal agents without re-entering shared credentials.
- [`docs/routing-intelligence-contract.md`](./docs/routing-intelligence-contract.md) — model/backend/tool routing policy so agents know what to call, when, and with which scoped permissions.
- [`docs/tool-awareness-handoff.md`](./docs/tool-awareness-handoff.md) — full handoff document for the Phase F tool awareness layer: file inventory, six integration paths, configuration knobs, extension recipes, and verification. The reference for incorporating this layer into another project.
- [`docs/vault-sync-contract.md`](./docs/vault-sync-contract.md) — mandatory bidirectional Obsidian + Notion sync contract for conversations, actions, decisions, health reports, agent activity, and shared-context retrieval.
- [`templates/WORKFLOW.md`](./templates/WORKFLOW.md) — copyable coding-agent workflow contract for commercial/customer repos.
- [`runbooks/deployment-access.md`](./runbooks/deployment-access.md) — safe Railway/DigitalOcean access and read-only inventory workflow.
- [`runbooks/agent-zero.md`](./runbooks/agent-zero.md) — exact Agent Zero install and verification path that worked locally.
- [`runbooks/a0-connector.md`](./runbooks/a0-connector.md) — exact A0 host-bridge setup, launchd persistence, and Codex exposure.
- [`docs/cloud-computer-options.md`](./docs/cloud-computer-options.md) — when a cloud computer like Orgo AI is valuable vs unnecessary cost.
- [`docs/steipete-tool-intake.md`](./docs/steipete-tool-intake.md) — prioritized intake of Peter/steipete tools for Super Agent.

---

## Reading order if you're new

1. [`docs/hermes-first-install-walkthrough.md`](./docs/hermes-first-install-walkthrough.md) — fresh-machine Hermes install and Super Agent setup path. Use this first for Zions/customer installs. ~10 min.
2. [`STORY.md`](./STORY.md) — why this exists. ~5 min.
3. This README. ~3 min.
4. [`LAUNCH.md`](./LAUNCH.md) — get it running. ~5 min.
5. [`ARCHITECTURE.md`](./ARCHITECTURE.md) — the system shape, the four self-pillars in detail, the routing rules. ~10 min.
6. [`ETHOS.md`](./ETHOS.md) + [`ECOSYSTEM-PLAYBOOK.md`](./ECOSYSTEM-PLAYBOOK.md) — the discipline that keeps the pathology from coming back. ~5 min.
7. [`docs/commercial-packaging.md`](./docs/commercial-packaging.md) + [`docs/portfolio-agent-architecture.md`](./docs/portfolio-agent-architecture.md) — sellable tiers and multi-agent structure. ~10 min.
8. [`runbooks/agent-zero.md`](./runbooks/agent-zero.md) + [`runbooks/a0-connector.md`](./runbooks/a0-connector.md) — reproduce the local Agent Zero/A0/Codex bridge. ~10 min.
9. [`docs/cloud-computer-options.md`](./docs/cloud-computer-options.md) + [`docs/steipete-tool-intake.md`](./docs/steipete-tool-intake.md) — expansion decisions. ~10 min.
10. [`docs/EXECUTION-PLAN.md`](./docs/EXECUTION-PLAN.md) — what ships in which session. ~5 min.
11. [`vault/decisions/openswarm-runtime-adoption.md`](./vault/decisions/openswarm-runtime-adoption.md) — OpenSwarm runtime + agent-builder design rationale, multi-instance correctness, verification. ~10 min.
12. [`docs/tool-awareness-handoff.md`](./docs/tool-awareness-handoff.md) — **incorporate the tool awareness layer into another project.** Six integration paths, file inventory, configuration knobs, extension recipes, verification. ~15 min. Use this when you want what's in the "Tool awareness" section above to live in a different codebase.

## License

MIT.
