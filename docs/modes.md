# Modes — Saiyan vs Super-saiyan

Two install modes, one repo, one share link. This doc explains what's actually in each mode, when to pick which, and how to upgrade later.

## TL;DR

| | Saiyan (lite) | Super-saiyan (full) |
|---|---|---|
| **For** | You already have a Hermes / Python agent project | You're starting fresh, want the full fleet |
| **What gets installed** | Planner + 14 in-process runtimes + 16 SKILL.md files, copied into your project | NATS + Temporal + Coordinator + Archon + Admiral on Railway, plus the skills layer baked in |
| **New infrastructure** | None | 5 Railway services, optional DigitalOcean VPSes on demand |
| **Cost floor** | $0 (you keep your existing setup) | ~$45/mo + LLM usage |
| **Install time** | ~3 minutes | ~30 minutes |
| **Install command** | `python3 install.py --mode=saiyan --target=/path/to/your/project` | `python3 install.py --mode=super-saiyan` |
| **Best when** | "I want the planner and tool catalog inside my existing Hermes" | "I want the full multi-agent fleet, fan-out, VPS spawning, the works" |

If unsure, start saiyan. Upgrading to super-saiyan later doesn't undo anything.

---

## What saiyan mode contains (in depth)

When you run `install.py --mode=saiyan --target=YOUR_PROJECT`, the script copies the following into your project. Nothing is run on Railway. Nothing requires NATS or Temporal. Everything runs in-process inside whatever Hermes you already have.

### `agent_os/orchestrator/` (~1,300 lines)

| File | Lines | What it does |
|---|---|---|
| `tier_classifier.py` | 134 | Classify each job as Tier 1 (auto), 2 (plan card + 'yes' to run), or 3 (hard stop, requires uppercase YES). Rules tunable in `config/tiers.yaml`. |
| `tool_planner.py` | 261 | Score every registered tool against the job. Return a `ToolPlan` with primary tool, alternatives, tier, cost/time estimate, model recommendation, and a `permanent_resource` flag for spawn-intent jobs. |
| `model_planner.py` | 110 | Pick the model deterministically (no LLM call). Seven models registered in `config/models.yaml`. Architecture / debug / security work auto-pairs `gpt-5.5 ↔ claude-opus-4.7` for dual-frontier review. |
| `plan_card.py` | 180 | Render the plan into Markdown / JSON / `/why` long-form. Tier 3 cards print an explicit `⚠ Permanent infra` warning when the job will provision a VPS or Railway service. |
| `intent_classifier.py` | 162 | Pure regex pass over the prompt. Detects spawn intent, fan-out intent, outbound phone/email. Adds tags so the planner picks the right runtime AND the tier gate fires. No LLM call, no fuzzy matching, no surprises. |
| `catalog.py` | 264 | Build `vault/graph/tool-catalog.yaml` from the SKILL.md files + identity packs + model registry. Single source of truth for the planner. |
| `adapters/job_router.py` | 177 | `Job` dataclass + `route()` (tag → runtime) + `dispatch()` (runtime → invoke). Saiyan-mode `dispatch()` only knows the 14 in-process runtimes; asking for a fabric runtime raises a friendly `RuntimeError` pointing at super-saiyan. |
| `adapters/plan_overrides.py` | 105 | Parse `/cancel /use /why /tier N YES` from any channel. Returns a structured `Override`. |
| `adapters/vault_memory.py` | 29 | Vault read/write adapter. |
| `config/models.yaml` | data | 7 models: Claude Opus 4.7, Sonnet 4.7, Sonnet 4.6, GPT-5.5, Kimi K2, DeepSeek v4 Pro, Gemini 2.5 Pro. Per-Mtok pricing, task-class tags, dual-frontier review pairs. |
| `config/tiers.yaml` | data | Tier rules. Spawn tags (`spawn-superagent`, `vps-spawn`, `build-specialist`, `archon`, `hire`, `permanent-agent`) are forced to Tier 3. Tunable without code changes. |
| `config/identities/*.yaml` | data | Identity packs (COO, GTM, Head of Ops). Each declares `tools_allowed`, `tools_denied`, `default_tier_ceiling`. |

### `agent_os/runtimes/` (14 in-process runtimes)

Each runtime has an `invoke.py` exposing `def invoke(job) -> RuntimeResult` (sync) or `async def run(job)` (async). They're called by `dispatch()` and they all run inside your Hermes process — no network, no event bus, no Temporal.

| Runtime | What it does |
|---|---|
| `hermes_self` | The default. Single Anthropic / OpenAI / DeepSeek / Moonshot / Gemini / OpenRouter call. |
| `claude_subagents` | Claude Code subagents — direct, in-repo coding. |
| `codex_cli` | OpenAI Codex CLI — background coding. |
| `aider` | Git-aware incremental coding. |
| `claude_managed` | Anthropic Claude Managed Agents — long-running cloud tasks. |
| `openclaw` | Autonomous-grind, shell, file-ops. |
| `openswarm` | Multi-agent deliverable production (slides, decks, research, charts) + agent-builder. |
| `browser_use` | Structured browser automation. |
| `agent_zero` | Visual / autonomous browser UI. |
| `computer_use` | Anthropic Computer Use SDK — raw desktop. |
| `e2b` | Sandboxed code execution (clean VM per run). |
| `exa` | Exa neural search. |
| `livekit` | Voice / realtime channel. |
| `terminal` | Plain cron-style scripts. |

### `vault/skills/active/tools/` (16 SKILL.md files)

One markdown file per runtime + `_catalog.md`. Frontmatter declares `tier`, `cost_class`, `risk_class`, `preferred_models`, `category`. The body explains *when to use*, *when NOT*, *alternatives*, *examples*. The planner's catalog reads these to score tools against jobs.

---

## What's NOT in saiyan mode (only in super-saiyan)

These live only in `hermes-super-agent` itself. Saiyan mode skips them on copy.

| Not in saiyan | Reason |
|---|---|
| `agent_os/bus/` (NATS publisher + subscriber) | Needs a running NATS server |
| `agent_os/workflows/` (Temporal workflows) | Needs a running Temporal server |
| `agent_os/a2a/` (FastAPI A2A server) | Needs FastAPI + uvicorn deployed |
| `agent_os/channels/telegram/` | The Admiral Telegram bot |
| `agent_os/orchestrator/{bootstrap,spawner,vps_provisioner,boot}.py` | Provision DigitalOcean VPSes via SSH bootstrap |
| `agent_os/runtimes/{a2a_delegate,coordinator,retell_channel,vps_spawn}/` | All depend on the fabric layer above |
| `vault/skills/active/tools/{archon_builder,coordinator,retell_channel}.md` | Describe fabric runtimes |
| `deploy/`, `scripts/setup.sh`, `scripts/deploy.sh` | Railway deploy automation |

If your saiyan-installed planner asks for one of these (because the user said "spin up a cold email superagent" and the intent classifier added the `spawn-superagent` tag), `dispatch()` raises:

```
RuntimeError: runtime 'vps_spawn' needs the super-saiyan fabric layer
(NATS + Temporal + Coordinator + spawner). Re-run install.py with
--mode=super-saiyan, or install the full fabric:
https://github.com/jbellsolutions/hermes-super-agent
```

Honest about the boundary, points the user at the fix.

---

## Upgrade path: saiyan → super-saiyan

You don't need to uninstall saiyan to upgrade. The two layers compose:

1. Keep saiyan installed in your existing Hermes project. The local planner and skills layer stay live there.
2. Clone `hermes-super-agent` separately. Run `install.py --mode=super-saiyan`. Five Railway services come up.
3. Point your local Hermes at the new Admiral's A2A endpoint via env var.
4. Now your local Hermes can delegate tasks to the Railway fleet via A2A — and the Railway fleet can spawn Tier 2 superagent VPSes.

The skills code is the same in both places (saiyan mode copies a snapshot, super-saiyan ships the live source). If you ever want to refresh saiyan to match super-saiyan, re-run `install.py --mode=saiyan --target=YOUR_PROJECT --force`.

---

## Cost breakdown

### Saiyan mode

| | Cost |
|---|---|
| Infrastructure | $0 |
| LLM API usage | Whatever your existing Hermes already spends |
| Total incremental | **$0/mo** |

### Super-saiyan mode

| | Cost |
|---|---|
| Railway (5 services: NATS, Temporal, Coordinator, Archon, Admiral) | ~$40/mo |
| Anthropic API (light usage) | $5–50/mo |
| Tier 2 superagent VPSes | $5/mo each, only when spawned |
| Retell AI phone (when calling) | $0.05/min |
| Instantly.ai email (per campaign) | usage-based |
| AgentOps | free tier covers most usage |
| **Floor** | **~$45/mo** |

The Coordinator has hard caps (`COORDINATOR_MAX_SUBTASKS=300`, `COORDINATOR_MAX_RETAINED=1000`) so a hostile or confused prompt can't melt your bill. Cost guardrails fire a NATS alert at 80% of `DAILY_COST_CAP_USD` and hard-block at 100%.

---

## When to pick which

**Pick saiyan if:**
- You already have a working Hermes / Python agent project
- You want the planner, tier gates, override surface, and tool catalog without managing 5 Railway services
- You're prototyping
- You want to stay at $0 incremental infra
- You don't need fan-out (or your existing setup already handles it)
- You don't need to spawn permanent specialist VPSes

**Pick super-saiyan if:**
- You're starting fresh — no existing Hermes
- You want fan-out across N parallel sub-agents (Coordinator + Temporal)
- You want to spawn permanent superagents on demand ("hire a cold-email specialist")
- You want a Telegram bot that ties the fleet together
- You're building a multi-agent product, not just adding skills to an existing one

When in doubt: start saiyan. ~3 minutes to install. Upgrading later costs nothing extra.
