<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <strong>Hermes Super Agent</strong><br/>
  <em>The fabric that turns one agent into a fleet.</em>
</p>

<p align="center">
  <a href="#get-it-running">Get it running</a> ·
  <a href="#what-it-actually-does">What it does</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="QUICKSTART.md">Quickstart</a> ·
  <a href="ARCHITECTURE.md">Architecture</a>
</p>

---

## Why this exists

You spun up a Hermes agent. It works. You ask it to do real work and it… runs out of room.

It can't fan one task across 300 parallel sub-agents. It can't spawn its own teammates. It can't survive a reboot mid-job. It can't tell you what it's doing in real time. It can't take a phone call. It can't read a Slack thread, finish the work overnight on a fresh VPS, and ping you on Telegram when it's done.

You don't need a smarter model. You need a **fabric** underneath the agent that does all of that for you.

That's what this is.

---

## What you get when this is running

You text Hermes on Telegram: *"Spin up a cold-email superagent with its own swarm coordinator and a phone agent."*

Twelve minutes later:

- A new VPS is online (DigitalOcean, $5/mo)
- A full Hermes is running on it, talking the same A2A protocol the Admiral does
- It has its own Kimi K2.6 coordinator wired in
- It has a Retell AI phone agent it owns
- It's heartbeating to your Admiral over NATS
- All three are auto-instrumented in AgentOps so you can see cost, latency, errors in one dashboard
- Tier 3 jobs (production deploys, outbound sends, anything destructive) are gated behind a one-line "YES" reply
- You go to bed. It runs the campaign. You wake up to a summary.

That's the promise. Below is exactly how it does it, and how to set it up tonight.

---

## What it actually does

Five things, all live, all tested, all behind a single Telegram bot:

| | What you can ask for | What happens under the hood |
|---|---|---|
| 1 | "Run this 300 ways in parallel and give me the best one." | The Coordinator service fans out to N sub-agents (Kimi K2.6 native, or any Anthropic / OpenAI / DeepSeek / Gemini / Moonshot / OpenRouter model) wrapped in a Temporal workflow so it survives crashes. |
| 2 | "Spin up a [domain] superagent for me." | The Spawner provisions a real VPS, SSH-bootstraps Docker + uv + the full Claude Code + Codex + Aider toolchain, drops in an `AGENT.md` for the new identity, starts the same A2A FastAPI server, registers with NATS. ~10 minutes. |
| 3 | "Build me a [linkedin / outbound-X / research-Y] specialist." | Archon (open-source meta-agent) generates the new agent's `AGENT.md` + skill files + Railway config from a natural-language spec. Specialist deploys to Railway and joins the fleet. ~15 minutes. |
| 4 | "Send a cold email" or "place a phone call." | Same brain (the COO Specialist), two channels: Instantly.ai for email, Retell AI for phone. Tier 3 hard-stop on both. |
| 5 | "What's everybody doing right now?" | Admiral subscribes to `agents.>` on NATS JetStream and forwards every fleet alert to Telegram. No polling. Sub-millisecond. |

And underneath all five: a planner that picks the right tool, the right model, and the right tier *before* anything runs. So you see the plan card first. You can `/use <tool>` to override, `/why` for the rationale, `/cancel` to abort, or `YES` (uppercase, deliberate) to greenlight a Tier 3.

---

## How it works

Three open-source primitives. None of them new, none of them ours. The trick is what happens when you snap them together.

### 1. Google A2A Protocol — the universal language

Every agent in the fleet exposes three HTTP routes and one JSON file:

```
GET  /agentCard          → what I can do, what I cost, how to reach me
POST /messages           → here's a task, run it
GET  /tasks/{task_id}    → status: submitted → working → completed
```

Cards are self-describing. Admiral reads them at boot and builds a live capability map. Adding a new specialist (Hermes-based, Kimi-based, Agent Zero, Archon, or anything that speaks A2A) does not require a code change in Admiral. It's just a new card.

### 2. NATS JetStream — the event bus

Every agent publishes to a namespaced subject:

```
agents.{id}.heartbeat
agents.{id}.task.started   .progress   .completed   .failed
agents.{id}.alert
fleet.commands.{id}
```

Admiral subscribes to `agents.>` (wildcard). State is live, not polled. JetStream persists, so a restart replays missed events and you never lose a fleet update. There's a circuit breaker in front of every publisher so a NATS outage degrades to "agents keep working, you just don't see them in real time" instead of "everything crashes."

### 3. Temporal — durable execution

The fan-out workflow is a Temporal workflow, not a best-effort coroutine. If your VPS reboots while 200 of 300 sub-agents are mid-flight, Temporal resumes from the last completed activity. No "did the job finish?" uncertainty.

That's the whole stack. NATS at $5/mo on Railway, Temporal at $15/mo on Railway, the rest is usage-billed. Floor is $45/mo total infra.

---

## Get it running

You need three things on your laptop: `git`, `python 3.11+`, `uv` (one-line installer). On macOS: `brew install git uv`.

You need three accounts: Anthropic (Claude), Railway (hosts the fleet), Telegram via [@BotFather](https://t.me/BotFather). Sign-up takes ~10 minutes total.

Then pick one of these three.

### Path A — Have an agent set it up for you (recommended)

Open Claude Code, Codex, or any Hermes/Cursor session inside this repo and paste:

> *Set up Hermes Super Agent on this machine. Read [`QUICKSTART.md`](QUICKSTART.md) for the exact steps. Verify `git`, `python 3.11+`, and `uv` are installed; install whatever's missing. Then walk me through every credential one at a time in plain English. For each service, tell me where to sign up, what to click, and what to paste back to you. Set up the required ones first (Anthropic, Telegram, Railway), then ask whether I want any of the optional ones (DigitalOcean for VPS spawning, Retell AI for phone, Instantly for cold email, AgentOps for dashboards). Write everything to `.env` at the repo root. Then run `./scripts/deploy.sh`. When it's done, send a `hello` to my Telegram bot and confirm it replies. Don't write code. I'll paste keys.*

The agent will:

1. Check your local prereqs and install anything missing
2. Walk you through each signup with the exact URL, exact button text, exact key to copy back
3. Skip the optional services unless you want them
4. Write `.env`
5. Deploy to Railway
6. Verify the Telegram round-trip

You won't write code. You will paste keys. ~25 minutes start to finish.

### Path B — Run the wizard yourself

Two scripts, three accounts, ~30 minutes. Full doc at [QUICKSTART.md](QUICKSTART.md).

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
./scripts/setup.sh      # interactive, asks for each key with the URL where to grab it
./scripts/deploy.sh     # spins up NATS → Temporal → Coordinator → Archon → Admiral on Railway
```

Idempotent. Re-run either script any time to update keys or redeploy.

### Path C — You already have it cloned and just want to wire fabric on top

Already running Hermes locally? Already have an Anthropic key in your shell? Skip the wizard:

```bash
cd hermes-super-agent
uv sync
cp .env.example .env    # edit by hand
./scripts/deploy.sh
```

---

## What gets deployed

Five Railway services (one click each, the script does it for you):

```
You ←→ Telegram ←→ Admiral (Railway)
                     │
                     ├── NATS JetStream    (event bus, $5/mo)
                     ├── Temporal          (durable workflows, $15/mo)
                     ├── Coordinator       (fan-out engine, model-pluggable)
                     ├── Archon            (agent builder)
                     │
                     └── Spawned superagents → DigitalOcean ($5/mo each, only when spawned)
```

Each spawned superagent is a real VPS running the same FastAPI A2A server you're running. It has Claude Code, Codex CLI, Aider, Docker — the full toolchain. API keys are forwarded over SSH at process start, never written to disk on the VPS.

---

## Real things you can ask it to do

These all work today on a fresh deploy. None are roadmap.

```
"summarize the news on AI safety today"
"research these three startups: Anthropic, OpenAI, Mistral. parallel."
"draft a Tier 1 email to garry@ycombinator.com about my super-agent fabric"
"build a LinkedIn outreach specialist that posts twice a week"
"spin up a cold email superagent with its own Kimi coordinator"
"what's the fleet doing right now"
"call (555) 123-4567 — pitch the COO consulting offer, log the transcript"
"deploy the GTM specialist to production"   ← Tier 3, asks for YES
```

Every one of those goes through the same pipeline: tier_classifier → tool_planner → model_planner → plan_card → (your approval if Tier 2/3) → dispatch → NATS event → result.

---

## What's actually in the box

| | |
|---|---|
| **Orchestrator** | Hermes — persistent memory, identity packs, planner + dispatcher + override surface |
| **Channels** | Telegram bot (long-poll), web (HTTP A2A), Slack/voice scaffolded |
| **Fan-out** | Coordinator service — model-pluggable, Temporal-wrapped, fan-out via Kimi K2.6 native or any model |
| **Spawning** | Tier 1 (Railway via Archon, ~15 min) + Tier 2 (DigitalOcean VPS via SSH bootstrap, ~10 min) |
| **Outbound** | Retell AI phone + Instantly.ai email — single COO Specialist brain, two channels, Tier 3 by default |
| **Coding** | Claude Code subagents (interactive) + Codex CLI (background) + Aider (git-aware incremental) |
| **Browser** | browser-use (structured) + Agent Zero (visual/autonomous, Dockerized) |
| **Search** | Exa neural search |
| **Sandbox** | E2B clean VM per run |
| **Observability** | NATS event stream + AgentOps SDK auto-instrumentation across all 7 model backends |
| **Tier gating** | tier_classifier.py rules, plan_card.py rendering, plan_overrides.py command parser |
| **Identity** | YAML-defined identity packs with `tools_allowed` / `tools_denied` / `default_tier_ceiling` |

Seven models in the registry: Claude Opus 4.7, Claude Sonnet 4.7, Claude Sonnet 4.6, GPT-5.5, Kimi K2, DeepSeek v4 Pro, Gemini 2.5 Pro. Architecture / debug / security work auto-pairs `gpt-5.5 ↔ claude-opus-4.7` for dual-frontier review. The model planner is rule-based and deterministic. No LLM call to pick the model.

---

## Tier-gated UX (so you stay in control)

| Tier | When | What happens |
|---|---|---|
| **1** | Read-only, cheap, idempotent | One-line banner: `⚡ using openswarm · claude-opus-4.7` |
| **2** | Mutates / substantive | 4-line plan card, reply `yes` to run, or `/use <tool>` `/why` `/cancel` |
| **3** | Destructive / public / >$1 | Hard stop. Reply `YES` (uppercase, deliberate) to proceed. |

Override commands work in any channel:

| Command | Effect |
|---|---|
| `/cancel` | Abort the pending plan |
| `/use <tool>` | Swap the runtime |
| `/use <tool> <model>` | Swap both |
| `/why` | 5-line rationale: tools scored, signals fired, model picked |
| `/tier <1\|2\|3>` | Force this task to a tier |
| `YES` (uppercase) | Confirm a Tier 3 |

---

## What it costs

| | Monthly |
|---|---|
| Railway (5 services: NATS, Temporal, Coordinator, Archon, Admiral) | ~$40 |
| Anthropic API (light usage) | $5–50 |
| Tier 2 superagent VPSes | $5/mo each, only when spawned |
| Retell phone | $0.05/min when calling |
| Instantly email | per-campaign |
| AgentOps | free tier covers most usage |
| **Floor** | **~$45/mo** |

No surprise costs. The Coordinator has hard caps (`COORDINATOR_MAX_SUBTASKS`, `COORDINATOR_MAX_RETAINED`) so a hostile or confused prompt can't melt your bill. Cost guardrails fire a NATS alert at 80% and hard-block at 100%.

---

## Status

The fabric is shipped behind 320 passing unit + smoke + integration tests. The seven recent architectural fixes (loop 20) wired the planner output through dispatch, switched A2A delegation to plain REST, fixed the email-routing gap, aligned model defaults across runtimes, and split Admiral vs worker roles so spawned VPSes don't fight for the Telegram bot token. Commit history is real — every "loop" is a discrete fix bundle with its own test sweep.

What's stubbed (and clearly marked in `docs/EXECUTION-PLAN.md`):

- The auto-update daemon ("self-growing") — wiring exists, the nightly cron is opt-in
- The quality flywheel ("self-learning") — `/agi-research` skill works on demand, the nightly auto-rollup is opt-in
- The self-healing loop — heartbeat + alert path is live, the auto-fix step from the genome library is on the next milestone

The five capabilities at the top of this README are live. The four "self-" pillars are real but partially manual today. Don't let anyone tell you otherwise.

---

## Reading order

1. [QUICKSTART.md](QUICKSTART.md) — get it running, ~30 min
2. [SETUP.md](SETUP.md) — what `setup.sh` and `deploy.sh` do under the hood
3. [ARCHITECTURE.md](ARCHITECTURE.md) — the system shape, planner contracts, dispatch flow
4. [STORY.md](STORY.md) — why this exists, the 14 frameworks it replaced
5. [ETHOS.md](ETHOS.md) — the rules that keep it from sprawling again
6. [SECURITY.md](SECURITY.md) — secret model, threat surface, where to send disclosures
7. `vault/decisions/` — every non-obvious choice, with the rationale and the alternative considered

---

## Hard rules

- **Never edit `vendor/`.** Open an upstream PR or wrap in `src/agent_os/runtimes/`.
- **Never start another framework wrapper.** New ideas land as runtime adapters, Hermes skills, or upstream contributions.
- **Single-state guarantee.** Every channel writes through the vault adapter. No per-channel state.
- **Default to Hermes.** Specialist runtimes are exceptions, not defaults. The planner enforces this.
- **Tier 3 always asks for YES.** No exceptions, no autopilot, no "the user already said yes once."

---

## License

MIT. Use it, fork it, ship it.

Security disclosures: [SECURITY.md](SECURITY.md).

Built by [Justin Bell](https://github.com/jbellsolutions). Architecture review credits in `vault/decisions/`.
