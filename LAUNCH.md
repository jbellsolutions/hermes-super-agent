# Launch Super Agent

> *Drop the link. Walk through it. Get rolling.*

This is the conversational launch flow. Three paths — pick the one that matches how you work:

| Path | Who it's for | How |
|---|---|---|
| **A — Claude Code/Codex (recommended)** | You already use an AI coding agent | Drop the repo URL into Claude Code or Codex. The setup instructions drive the rest in plain English. |
| **B — One-command bootstrap** | You want a single shell script | `./scripts/launch.py` walks you through every prompt. |
| **C — Self-driving (Hermes does it)** | You want the agent to set itself up | Bootstrap with minimum keys, then ask Hermes "set yourself up." It uses OpenClaw + Computer Use to fill in the rest. |

---

## Path A — Hermes-first Claude Code or Codex setup (recommended)

Drop this in a Claude Code or Codex session, anywhere:

> *"Set up a Hermes Super Agent for me. Repo: https://github.com/jbellsolutions/hermes-super-agent. Start by checking whether Hermes Agent is installed. If Hermes is missing, install it from the official Hermes installer. Then interview me in plain English, ask only for the keys needed for my chosen tier, connect the shared Obsidian/Notion brain if available, and verify everything before you say it is ready."*

Claude Code will:

1. **Check for Hermes first** — `command -v hermes`, `hermes --version`, `hermes doctor`.
2. **Install Hermes if missing** using the official Nous Research installer.
3. **Run/guide `hermes setup`** to configure provider/model, terminal, memory, tools, and gateway.
4. **Clone the repo** with submodules.
5. **Read [`docs/hermes-first-install-walkthrough.md`](./docs/hermes-first-install-walkthrough.md)** and `.claude/skills/agent-os/SKILL.md`.
6. **Walk you through `LAUNCH.md`** interactively, asking about:
   - Which product tier they want: Operator, Pro Operator, or Enterprise.
   - What business/project/offer the agent is being set up for.
   - What first workflows the agent should own.
   - Which channels you want active first: CLI, Telegram, Slack, web/API, or voice.
   - Which frontier models to connect first: GPT-5.5 and/or Claude Opus 4.6/4.7 for architecture/debug/security work, plus cheaper workers like DeepSeek when appropriate.
   - Which deploy target: local-only, Railway, Docker/VPS, Fly, DigitalOcean, or customer-isolated Enterprise.
   - Where the shared Obsidian vault lives and whether Notion credentials/database IDs are available.
   - Which keys you have ready vs need to grab.
7. **Stage your `.env`** with only the keys you provided. Never print secrets.
8. **Run `./scripts/bootstrap.sh`** if present/needed — installs `uv`, syncs Python, installs pnpm deps.
9. **Run tests** — prefer `PYTHONPATH=src uv run pytest -q` until packaging is normalized.
10. **Verify the shared-brain loop** — write a setup summary to Obsidian, write/update Notion if configured, then retrieve that context in a fresh prompt.
11. **Hand you the proof.** Briefs you on what is live, what is pending, and which tools were intentionally not installed.

Estimated time end-to-end: **15 minutes** if your keys are ready, **30–45 minutes** if you're collecting them as you go.

Commercial tier rule: Operator is the default. Pro Operator offers Agent Zero/A0 and the Tier 1 tool pack when prerequisites are met. Enterprise adds customer/project isolation, Railway/DigitalOcean/VPS discovery, and optional Orgo-style managed cloud computers. Orgo is never a default dependency.

---

## Path B — One-command bootstrap

If you don't want to use Claude Code for the setup itself:

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
./scripts/launch.py
```

`scripts/launch.py` is a Python wizard. It prompts for:

- **Operator name** (becomes your canonical identity in `vault/conversations/`)
- **Commercial tier** (`operator`, `pro-operator`, or `enterprise`)
- **Business/project name and business type**
- **First workflows** the agent should own
- **Human-approval rules** for risky actions
- **Default provider/model** for Hermes — OpenRouter is the default first-class path
- **OpenRouter/Anthropic/OpenAI key** for the chosen provider
- **Telegram bot token + allowed user ID** when you want Telegram access
- **Channels to enable** (Slack, Telegram, web text, web voice — pick any combination)
- **API keys** (you can skip optional ones and the relevant runtime stays disabled)
- **Deploy target** (Railway, Docker Compose, Fly, or local-only)
- **Voice realtime provider** (OpenAI Realtime / Gemini Realtime / disabled)

It starts with a Hermes Agent preflight. If `hermes` is missing, the wizard installs Hermes from the official Nous Research installer first. Then the Super Agent wizard performs the essential Hermes quickstart configuration itself: provider/model, provider key, and Telegram env values when provided. After that it writes your repo `.env`, syncs Hermes' own env/config, runs `uv sync` and `pnpm install`, runs smoke tests, and tells you to launch real Hermes with `hermes` / `hermes doctor`. `uv run agent-os boot` is currently a Stage 2 scaffold diagnostic, not the live Hermes launcher.

The wizard is idempotent — re-run it any time to change settings.

---

## Path C — Self-driving setup (Hermes drives)

This is the most interesting path. You give Hermes the absolute minimum and let it use its own runtimes to set itself up.

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
./scripts/launch.py --minimal   # asks for provider key, operator, and Telegram quick access
hermes doctor                   # verify actual Hermes install
hermes                          # start real Hermes CLI chat
```

Then in your terminal (Hermes opens a CLI session by default with no keys configured):

> *"Set yourself up. I want Slack + Telegram + the web voice mode. I have keys in 1Password under 'agent-os/*'. Deploy to Railway when you're ready."*

Hermes will:

1. **Ask Computer Use** (via the runtime adapter) to open 1Password and fetch the keys you named, dropping them into `.env` for you.
2. **Ask OpenClaw** to verify each key resolves (a quick `curl` to each provider's `/me` or equivalent).
3. **Run `agent-os manifest`** itself to populate its system graph.
4. **Ask Claude Code subagents** to write the per-channel onboarding configs based on the keys it has.
5. **Run the smoke tests** itself.
6. **Deploy via Railway CLI** if `RAILWAY_TOKEN` was in your password manager.
7. **Post you a Slack DM** when it's running, summarizing what's live and what isn't.

This is the dogfood test of the architecture. If Hermes can stand up the rest of agent-os from minimum config, the runtime tool belt is real. If it can't, you've found the seam — and that's a useful seam to find on day one.

> *Note: Path C is currently scaffolded but the full self-setup loop won't run end-to-end until stages 3–10 of `docs/EXECUTION-PLAN.md` are wired. Until then, Path A or B will get you running; Path C is the destination.*

---

## What you need before launch

### Always required
- **Hermes Agent install path** — if `hermes` is already installed, `hermes --version` and `hermes doctor` should pass. If missing, `./scripts/launch.py` installs it first from the official Nous Research installer, then continues the wizard.
- **Provider key for your default model** — OpenRouter is the default first-class path; Anthropic/OpenAI are also supported.
- **Telegram access values if wanted** — `TELEGRAM_BOT_TOKEN` from BotFather plus numeric `TELEGRAM_ALLOWED_USERS`.
- **Operator name** — the canonical identity that ties Slack/Telegram/web/voice to one conversation log.
- **Tier** — Operator, Pro Operator, or Enterprise.
- **Business/project context** — name, offer/business type, first workflows, and approval rules.
- **Shared brain path** — Obsidian vault path; Notion integration/database IDs when available.

### Per-channel (pick at least one)
- **Slack** — `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`. [Create a Slack app](https://api.slack.com/apps).
- **Telegram** — `TELEGRAM_BOT_TOKEN`. Talk to [@BotFather](https://t.me/BotFather).
- **Web text chat** — no extra keys; runs on the local Next.js webapp.
- **Web voice** — `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (self-hosted or [LiveKit Cloud free tier](https://livekit.io)) **plus** `OPENAI_API_KEY` *or* `GEMINI_API_KEY` for the realtime voice model.

### Per-runtime (optional, enabled only if key present)
- **Codex CLI** — `OPENAI_API_KEY` (already used for voice if voice is on).
- **E2B** — `E2B_API_KEY` ([free tier](https://e2b.dev)).
- **Exa** — `EXA_API_KEY` ([free tier](https://exa.ai)).
- **OpenRouter** — `OPENROUTER_API_KEY` if you want non-Anthropic / non-OpenAI models.
- **Railway** — `RAILWAY_TOKEN` only when discovering/deploying Railway apps.
- **DigitalOcean** — `DIGITALOCEAN_ACCESS_TOKEN` only when discovering/managing droplets/apps.
- **Orgo AI** — `ORGO_API_KEY` only for Enterprise deployments that need an isolated visible cloud computer.

### Observability (optional, free if self-hosted)
- **Langfuse** — runs in your Docker Compose stack at `localhost:3000`. No external account needed.

### CRM/RevOps (optional, when you onboard verticals)
- **Apollo / Smartlead / HubSpot / Salesforce** — only when you onboard the SDR fleet or the GTM verticals.

---

## After launch

Once Hermes is installed and verified, you have three operating commands available in any Claude Code/Codex session inside the repo:

- `/agent-os` — orient yourself. Run after entering a session to see what's running, what's stubbed, what to do next.
- `/explain "..."` — query the system graph. *"What wrote my morning brief?"* *"How does the SDR fleet connect to the morning brief?"*
- `/route --tags ...` — see which runtime would handle a hypothetical job, useful when designing a new vertical.

Plus four advanced skills:
- `/manifest` — rebuild the system graph after adding a new component.
- `/heal` — manually trigger the self-healing state machine.
- `/agi-audit` — score a target with the agi-1 audit.
- `/agi-research` — kick off a Karpathy autoresearch loop on a stalled skill.

---

## Daily life with agent-os

Three things happen automatically every day, no human in the loop:

1. **02:00 — the upgrader runs.** Pulls Hermes / OpenClaw / browser-use / Aider / Codex / agi-1 / awesome-hermes-agent. Smokes each. Promotes the green ones. Quarantines the red ones with a Slack alert. Logs everything to `vault/upgrades/<date>.yaml`.
2. **02:30 — `/agi-audit` runs against the day's outputs.** Scores `vault/runs/`. Flags regressions. Writes the journal to `vault/daily/<date>.md`.
3. **Throughout — the self-healing loop ticks every 5 minutes.** Polls heartbeats, validators, cron schedule, API health, cost guardrails. Failures match against the genome and auto-fix when they're known patterns; spawn a 3-agent diagnostic council when they aren't.

You wake up. The system has improved itself by a tiny bit. New community skills are staged for review. Yesterday's fixes are in the genome. Costs are under budget or you got a Slack alert at 80%. Repeat.

---

## What to do when something breaks

**Slack alert: "smoke red on stream X"** → Open the dashboard, see the diff that failed. Either approve a manual fix and re-promote, or skip this upgrade and let the next nightly try again.

**Hermes stops responding in Slack** → The heartbeat will catch it within 5 minutes and restart. If it doesn't, `uv run agent-os heal` runs the loop manually. If that doesn't work, `vault/incidents/` has the diagnostic council's last verdict.

**A specialist runtime errors** → Job router falls back to Hermes itself for the duration. Specialist re-enters rotation when its smoke is green again.

**Vendor module went stale (90+ days no upstream commits)** → `vendor_health` stream flags it. You decide whether to wait, contribute upstream, or switch to an alternative.

---

## Common questions

**"Can I use my own model instead of Claude?"** Yes. Set `HERMES_DEFAULT_MODEL` in `.env`. Hermes is bring-any-model — works with OpenRouter (200+ models), Nous Portal, NVIDIA NIM, OpenAI, Gemini, your own endpoint.

**"Can I run without OpenClaw?"** Yes — it's optional. The router falls back to Hermes itself for autonomous-grind jobs. You'll lose some battle-tested execution surface but the system still works.

**"Can I disable the upgrader?"** Set `UPGRADER_CRON=` (empty) in `.env`. Then submodules stay pinned. You lose the daily-evolution moat.

**"Can I run multiple agent-os instances?"** Yes — but they should NOT share a vault. Each instance owns its own conversation logs and heartbeats. If you want shared memory across instances, that's a multi-tenant feature and lives in `examples/multi-tenant/` (not yet built).

**"Should one Hermes agent run all my businesses?"** No. Use the hub-and-spoke model in `docs/portfolio-agent-architecture.md`: one primary Hermes Super Agent as portfolio operator, plus isolated specialist agents/workspaces for serious businesses, clients, or Paperclip companies.

**"Are the steipete Tier 1 tools default?"** They are default recommended candidates for Pro Operator, not mandatory dependencies. The installer should offer them one at a time, install only relevant tools, and smoke-test each before promotion.

**"How do I add a new vertical app?"** `examples/<your-vertical>/` directory + a `manifest.yaml` declaring its agents, tools, data sources, outputs, and consumers. The manifest aggregator picks it up on the next run; the system graph adds it; `/explain` knows about it.

**"How do I add a new specialist runtime?"** `src/agent_os/runtimes/<name>/` with `__init__.py`, `invoke.py`, `manifest.yaml`. Add a router rule. Add an upgrader stream + smoke if vendored. See `CONTRIBUTING.md`.

**"Can I roll back an upgrade?"** Yes — every upgrade is logged with the from/to commit SHAs in `vault/upgrades/`. The dashboard has a one-click rollback. The CLI has `agent-os upgrade --rollback <stream>`.

---

## The bar

When all three of these are green, you're running:

```bash
hermes doctor                         # real Hermes health check
hermes                                # real Hermes CLI starts
uv run agent-os manifest              # Super Agent graph builds
```

`uv run agent-os boot` is currently a scaffold diagnostic for Stage 2 wiring. If it prints `status: scaffold_not_error`, that is expected; use `hermes` to start the actual agent.

When all five accessibility criteria pass — same conversation across Slack/Telegram/voice; cross-channel file context; streaming chat; sub-2s voice round-trip; one-command deploy — you're shipping.
