# Ecosystem Playbook — Layering, Not Switching

The Nate Jones thesis: the agent market is moving toward LAYERS, not one-product-to-rule-them-all. Stop asking "which agent should I switch to?" Start asking "which layer is each piece of work the right shape for?"

## The layer stack (every role filled by a tool with momentum)

| Layer | Tool | Notes |
|---|---|---|
| 1. Default model (where the model IS the work) | **Claude Code + Opus 4.7** | Direct, unwrapped, at the keyboard. Don't replace. |
| 2. Always-on orchestrator (work happens while you sleep) | **Hermes**, vendored, daily-updated | Wired in `packages/orchestrator/` — see `ARCHITECTURE.md`. |
| 3. Autonomous heavy-execution (long shell/file/browser grind) | **OpenClaw**, optionally sandboxed by **NemoClaw** when GA | Wired in `packages/runtimes/openclaw/`. |
| 4. Structured browser automation | **browser-use** | Wired in `packages/runtimes/browser_use/`. |
| 5. Raw desktop / native apps | **Anthropic Computer Use SDK** | `packages/runtimes/computer_use/`. |
| 6. Coding (interactive) | **Claude Code subagents** | `packages/runtimes/claude_subagents/`. |
| 7. Coding (background, multi-provider hedge) | **Codex CLI**, **Aider** | `packages/runtimes/{codex_cli,aider}/`. |
| 8. Long-running cloud jobs | **Anthropic Claude Managed Agents** | `packages/runtimes/claude_managed/`. |
| 9. Sandboxed code execution | **E2B** | `packages/runtimes/e2b/`. |
| 10. Search-to-artifact | **Perplexity Personal Computer** (delegate via MCP) + **Exa** (programmatic) | `packages/runtimes/exa/`. |
| 11. Voice / realtime | **LiveKit + OpenAI Realtime API + Gemini Realtime API** | `packages/runtimes/livekit/` + `packages/channels/voice/`. |
| 12. Recurring Slack-native team workflows | **ChatGPT Workspace Agents** when routing-from-Slack > data depth; otherwise our orchestrator | Decision per-workflow. |
| 13. CRM/RevOps reach | **Salesforce Headless 360 + HubSpot MCP** | Hermes calls via MCP. Don't rebuild. |
| 14. Memory backstop | Hermes' native memory (default) → **Letta** or **mem0** if data volume forces it | `packages/runtimes/` adapter when promoted. |
| 15. Self-learning library | **DSPy** | Inside `packages/quality/`. |
| 16. Eval / regression | **promptfoo** | Inside `packages/quality/`. |
| 17. Observability / tracing | **Langfuse** (self-host, free) — optional **NVIDIA NeMo Agent Toolkit** for cross-framework metrics | `packages/observability/`. |
| 18. Durable cron + retry | **Inngest** when Hermes' light scheduling can't guarantee durability | `packages/upgrader/` and per-vertical when needed. |

## What every old framework repo becomes

| Old repo | Disposition |
|---|---|
| `agent-core` | Identity packs → Hermes config in `packages/orchestrator/config/identities/`. |
| `coo-agent` | Restart heuristics → upgrader smoke; Computer Use playbooks → OpenClaw configs. |
| `forge` | Swarm-design prompts → Hermes skill `vault/skills/_templates/design-swarm.md`. |
| `agent-company` | Meta→CEO→Lead→Worker pattern → Hermes skill `vault/skills/_templates/hierarchical-delegation.md`. |
| `ultimate-agent-framework` / `division-builder` | Division presets → Hermes identity-pack bundles. |
| `agi-1` | **Vendored as `vendor/agi-1`. Auto-updated. No code change.** |
| `agi-codex` | Folded into agi-1 as additional skills. |
| `titans-of-direct-response-mastermind-council` | Council engine → generic AGI-1 skill. Titans content stays in its own repo. |
| `coo-platform` / `coo-dashboard` / `operations-core` | Best of three → `packages/dashboard/`. |
| `gstack-framework` | Skill templates → `vault/skills/_templates/`. |
| `agentstack` / `agentstack-fleet-builder` | Skip — nearly empty. |
| `ops-os` / `paperclip-businesses` / `paperclip-operations-hub` | Heartbeat patterns + Paperclip MCP → Hermes config + MCP entries. |
| Vertical apps (`cold-email-agent`, `speakeragent-*`, `linkedin-autopilot`, `titans-*`, etc.) | Stay in their own repos. Each gets a `manifest.yaml`. They consume agent-os. |

## Day-to-day rule changes

- **Stop**: opening a new wrapper repo when frustrated. Frustration → upstream PR or `packages/runtimes/<name>/` extension.
- **Stop**: applying agi-1 to repos without an orchestrator. The flywheel needs an engine block. Now Hermes is the engine.
- **Start**: every new vertical app declares a `manifest.yaml` and consumes agent-os. SDR fleet, content engine, COO control room — they're examples in `examples/`, not new top-level frameworks.
- **Start**: when an ecosystem launch passes the 5-question filter, write a 1-page note in `vault/decisions/` and a small adapter in `packages/runtimes/<name>/`. That's how leverage compounds.
- **Start**: contributing upstream. If Hermes or OpenClaw is missing something you need, the PR is the leverage. Your name on a 100K-star repo > your 14th 0-star repo.

## What to NEVER add

- Anything with <2K stars or no commits in 60 days.
- Anything that wraps Hermes/OpenClaw/Claude Code rather than extending them.
- Yet another "agent framework" — agent-os exists because we have 14 of those.

## Super Agent additions

### Agent Zero + A0

Use Agent Zero when the job benefits from a visual autonomous UI. A0 is the bridge that lets Agent Zero operate against the host Mac. Keep Agent Zero bound to localhost unless explicitly changed.

### Codex in Super Agent

Codex is the preferred repo/code execution engine for implementation, test, refactor, and review work when a dedicated coding runtime is useful.
