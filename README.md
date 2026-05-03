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

Conversational Python wizard. It now starts with a Hermes Agent preflight: if `hermes` is missing, it installs Hermes from the official Nous Research installer before asking Super Agent questions. Then it asks for business context, tier, keys, approval rules, and deploy target; runs `uv sync` + `pnpm install`, runs the smoke tests, builds the manifest graph, and hands you a summary.

### Path C — Self-driving setup (Hermes drives)

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
./scripts/launch.py --minimal      # asks for model key + operator setup
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
│   ├── openclaw/    │   ├── browser_use/
│   ├── agent_zero/  │   ├── computer_use/
│   ├── claude_subagents/ ├── codex_cli/
│   ├── aider/       │   ├── claude_managed/
│   ├── e2b/
│   ├── exa/         │   ├── livekit/
│   └── terminal/
├── manifest/        # introspection — graph aggregator, MCP server, /explain backend
├── quality/         # agi-1 invocations — audit, council, autoresearch
├── upgrader/        # nightly auto-update daemon (10 streams)
├── channels/        # slack / telegram / web / voice — single-state guarantee
└── observability/   # Langfuse + optional NVIDIA NeMo Agent Toolkit

vendor/              # auto-updated upstream OSS — DO NOT EDIT
├── hermes-agent/    │   ├── openclaw/         │   ├── nemoclaw/  (parked)
├── browser-use/     │   ├── aider/            │   ├── awesome-hermes-agent/
└── agi-1/

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

1. **02:00** — the upgrader runs. Pulls Hermes / OpenClaw / browser-use / Aider / Codex / agi-1 / awesome-hermes-agent. Smokes each. Promotes the green ones. Quarantines the red ones with a Slack alert. Logs to `vault/upgrades/<date>.yaml`.
2. **02:30** — `/agi-audit` runs against the day's outputs. Scores `vault/runs/`. Flags regressions. Writes `vault/daily/<date>.md`.
3. **Every 5 minutes** — the self-healing loop ticks. Polls heartbeats, validators, cron, API health, cost guardrails. Auto-fixes known patterns; spawns a council for unknown ones.

You wake up. The system has improved itself a little. Yesterday's fixes are in the genome. Costs are under budget or you got a Slack alert at 80%. Repeat.

---

## Status — verified at scaffold time

```
✓ uv sync                         # all packages install cleanly
✓ uv run pytest -q                # 23 passed
✓ uv run agent-os route --tags ...# router returns correct runtime per tag
✓ uv run agent-os manifest        # 20 nodes, 57 edges built
✓ git submodule status            # 7 submodules pinned
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

## License

MIT.
