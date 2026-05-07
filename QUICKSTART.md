# Quickstart — From Zero to Live in ~30 Minutes

Two scripts, three accounts. That's the whole install.

If you'd rather have an agent walk you through it, paste the [master setup prompt](#master-setup-prompt-paste-into-claude-code--codex--cursor) at the bottom of this doc into Claude Code, Codex, or Cursor — it does everything below conversationally and you don't have to read another line.

---

## Before you start — sign up for these (~10 min)

### Required (the floor)

| Service | What for | Cost |
|---|---|---|
| [Anthropic Console](https://console.anthropic.com) | Claude API key | usage-billed |
| [Railway](https://railway.com) | Hosts the fabric (5 services) | ~$40/mo |
| [Telegram BotFather](https://t.me/BotFather) | Your interface to Hermes | free |
| [@userinfobot](https://t.me/userinfobot) | Get your numeric chat ID | free |

### Optional (skip on day one, add later)

| Service | What it unlocks |
|---|---|
| [DigitalOcean](https://cloud.digitalocean.com) | Spawning Tier 2 superagent VPSes |
| [Retell AI](https://retellai.com) | Outbound phone calls |
| [Instantly.ai](https://instantly.ai) | Cold email campaigns |
| [AgentOps](https://app.agentops.ai) | Cost / latency / error dashboard |
| [Moonshot](https://platform.moonshot.ai) | Kimi K2.6 native swarm coordinator |

You can re-run setup any time to add more keys. Everything is idempotent.

---

## Step 1 — Clone and prep your laptop (~5 min)

You need `git`, `python 3.11+`, and `uv`. On macOS:

```bash
brew install git uv
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
```

That's all the laptop needs. Everything else runs in the cloud.

---

## Step 2 — Run the interactive setup (~5 min)

```bash
./scripts/setup.sh
```

Walks you through every credential one at a time, with the URL where to grab each key. Press Enter to skip the optional ones.

**At minimum, paste:**

- Anthropic API key
- Telegram bot token (talk to [@BotFather](https://t.me/BotFather))
- Telegram chat ID (talk to [@userinfobot](https://t.me/userinfobot))
- Railway API token (`railway login` opens this; or grab it from Railway → Account → Tokens)

The script writes a `.env` file at the repo root. Re-run any time to add or update keys. Existing values are shown by their last 4 chars and kept on Enter.

---

## Step 3 — Deploy (~15–20 min, mostly Railway build time)

```bash
./scripts/deploy.sh
```

This:

1. Installs the Railway CLI if missing (Homebrew on macOS).
2. Logs you into Railway (browser opens once).
3. Creates a Railway project named `hermes-fabric`.
4. Spins up five services in order: **NATS → Temporal → Coordinator → Archon → Admiral**.
5. Wires the URLs across services automatically (so Admiral knows how to reach NATS, Coordinator knows how to reach Temporal, etc).
6. Sets every env var from your `.env` on the right service.
7. Prints a summary of public URLs at the end.

Builds finish in the background. Watch them at [railway.app/dashboard](https://railway.app/dashboard). Admiral takes ~5 min after the others go green.

---

## Step 4 — Talk to Hermes

Open Telegram, find your bot, send:

```
hello
```

Hermes should reply. You're live.

Try:

```
summarize the news on AI safety today
research these 3 startups: Anthropic, OpenAI, Mistral
spin up a cold email superagent           ← needs DO + Retell + Instantly keys
deploy the GTM specialist to production   ← Tier 3, asks for YES
```

---

## What to do if something breaks

| Problem | Fix |
|---|---|
| `setup.sh` can't write `.env` | Make sure you're in the repo root: `cd hermes-super-agent` |
| Railway CLI install fails | `brew install railway` manually, then re-run `./scripts/deploy.sh` |
| A service shows red in the Railway dashboard | Click the service → Logs. Almost always a missing key. Re-run `setup.sh` to fix and `deploy.sh` to redeploy. |
| Telegram bot doesn't respond | Check Admiral logs at railway.app/dashboard. Usually a bad bot token or a chat ID mismatch. |
| Bot replies "Ignoring message from unallowed chat_id=…" | Open Telegram, send `/start` to [@userinfobot](https://t.me/userinfobot), copy the numeric ID, re-run `setup.sh` and paste it as `TELEGRAM_CHAT_ID`. |
| `409 Conflict: another instance is polling` in logs | A second Railway replica is fighting for the bot token. Set Admiral's replica count to 1 in the Railway dashboard. |

Both scripts are idempotent. Existing services are updated, never recreated. Re-running is always safe.

---

## What you have running now

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

Each spawned superagent is a real VPS running the same FastAPI A2A server you're running. It has Claude Code, Codex CLI, Aider, and Docker. API keys are forwarded over SSH at process start, never written to disk on the VPS.

---

## Add more later

- **Tier 2 spawning:** sign up for DigitalOcean, paste the token via `setup.sh`, redeploy. Then from Telegram: *"spin up a cold email superagent."*
- **Outbound phone:** sign up for Retell AI, paste the API key + agent ID, redeploy.
- **Outbound email:** sign up for Instantly.ai, paste the key + campaign ID, redeploy.
- **Native Kimi swarm:** sign up for Moonshot, paste the key, redeploy. Coordinator picks up the model from `config/models.yaml`.

---

## Cost what-to-expect

| | Monthly |
|---|---|
| Railway (5 services) | ~$40 |
| LLM API usage (light) | $5–50 |
| Tier 2 superagent VPSes | $5/mo each (only when spawned) |
| Outbound phone (Retell) | $0.05/min when calling |
| **Floor** | **~$45/mo** |

The Coordinator has hard caps: `COORDINATOR_MAX_SUBTASKS=300` and `COORDINATOR_MAX_RETAINED=1000` by default. Cost guardrails fire a NATS alert at 80% of `DAILY_COST_CAP_USD` and hard-block at 100%. No surprise bills.

---

## Master setup prompt (paste into Claude Code / Codex / Cursor)

If you'd rather have an agent walk you through everything, paste this into any agent session inside the cloned repo:

> Set up Hermes Super Agent on this machine. Read `QUICKSTART.md` for the exact steps. Verify `git`, `python 3.11+`, and `uv` are installed; install whatever's missing. Then walk me through every credential one at a time in plain English. For each service, tell me where to sign up, what to click, and what to paste back to you. Set up the required ones first (Anthropic API key, Railway API token, Telegram bot token via BotFather, Telegram chat ID via @userinfobot), then ask whether I want any of the optional ones (DigitalOcean for VPS spawning, Retell AI for phone, Instantly.ai for cold email, Moonshot for native Kimi swarm, AgentOps for dashboards). Write everything to `.env` at the repo root. Run `./scripts/setup.sh` non-interactively if anything is missing, then run `./scripts/deploy.sh`. When deploy finishes, ask me to send `hello` to my Telegram bot and confirm it replies. Don't write code. I'll paste keys.

You'll paste keys. You won't write code. ~25 minutes start to finish.

---

## Next reading

- [README.md](README.md) — what this whole thing is, the offer, the mechanism
- [SETUP.md](SETUP.md) — detailed runbook of what `setup.sh` and `deploy.sh` do under the hood
- [ARCHITECTURE.md](ARCHITECTURE.md) — A2A + NATS + Temporal contracts, dispatch flow, planner internals
- [src/agent_os/orchestrator/config/identities/](src/agent_os/orchestrator/config/identities/) — edit identity packs (COO, GTM, Head of Ops) without touching code
