# Hermes Quickstart — From Zero to Live in 30 Minutes

Two scripts, three accounts. That's it.

---

## Before you start — sign up for these (10 min)

You'll need accounts at:

| Service | What for | Cost |
|---|---|---|
| [Railway](https://railway.com) | Hosts the fleet | ~$40/mo |
| [Anthropic Console](https://console.anthropic.com) | Claude API key | usage |
| [Telegram BotFather](https://t.me/BotFather) | Your interface to Hermes | free |

Optional (for advanced capabilities — skip on day one):
- [DigitalOcean](https://cloud.digitalocean.com) — for spawning Tier 2 superagent VPSes
- [Retell AI](https://retellai.com) — for outbound phone calls
- [Instantly.ai](https://instantly.ai) — for cold email
- [AgentOps](https://app.agentops.ai) — for cost/error dashboards

---

## Step 1 — Clone and prep your laptop (5 min)

You need `git`, `python 3.11+`, and `uv`. On macOS:

```bash
brew install git uv
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
```

That's all the laptop needs. Everything else runs in the cloud.

---

## Step 2 — Run the interactive setup (5 min)

```bash
./scripts/setup.sh
```

It walks you through every credential — pasting an API key one at a time, with the URL where to grab each one. Press Enter to skip the optional ones.

**At minimum, paste:**
- Anthropic API key
- Telegram bot token (talk to [@BotFather](https://t.me/BotFather))
- Telegram chat ID (talk to [@userinfobot](https://t.me/userinfobot))

The script writes a `.env` file at the repo root.

---

## Step 3 — Deploy (15–20 min, mostly Railway build time)

```bash
./scripts/deploy.sh
```

This:
1. Installs the Railway CLI if you don't have it (Homebrew on macOS).
2. Logs you into Railway (browser window opens once).
3. Creates a Railway project named `hermes-fabric`.
4. Spins up five services in order: **NATS → Temporal → Coordinator → Archon → Admiral**.
5. Wires the URLs across services automatically.
6. Sets every env var from your `.env` on the right service.

You'll see a summary of URLs at the end. The actual builds finish in the background — watch them at [railway.app/dashboard](https://railway.app/dashboard).

---

## Step 4 — Talk to Hermes

When the Admiral build finishes (~5 min), open Telegram, find your bot, and send:

```
hello
```

Hermes should reply. You're live.

Try:
- `summarize the news on AI safety today`
- `research these 3 startups: Anthropic, OpenAI, Mistral`
- `spin up a cold email superagent` (requires DO + Retell/Instantly keys)

---

## What if something goes wrong?

| Problem | Fix |
|---|---|
| `setup.sh` can't write `.env` | Make sure you're in the repo root: `cd hermes-super-agent` |
| Railway CLI install fails | `brew install railway` manually, then re-run |
| A service shows red in the Railway dashboard | Click the service → Logs. Most issues are missing API keys; re-run `setup.sh` to fix and re-run `deploy.sh`. |
| Telegram bot doesn't respond | Check Admiral logs at railway.app/dashboard. Usually a bad bot token. |

Re-running either script is safe. They're idempotent — existing services are updated, never recreated.

---

## What you actually have now

```
You ←→ Telegram ←→ Admiral (Railway)
                     │
                     ├── NATS (event bus)         Railway
                     ├── Temporal (durable jobs)  Railway
                     ├── Coordinator (fan-out)    Railway
                     ├── Archon (agent builder)   Railway
                     │
                     ├── Coordinator can run any model:
                     │   claude-sonnet-4-5, gpt-5, deepseek, gemini, kimi, ...
                     │
                     └── Spawned superagents      DigitalOcean (one VPS each)
```

Each spawned superagent is a full Hermes install with Claude Code, Codex, Aider, and Docker. They get your API keys forwarded over SSH (never written to disk on the VPS).

---

## Next steps

- **Add Tier 2 spawning:** sign up for DigitalOcean, run `./scripts/setup.sh` again, paste DO token. From Telegram: "spin up a cold email superagent."
- **Add outbound phone/email:** Retell + Instantly accounts, re-run setup, talk to Hermes.
- **Customize:** see [`SETUP.md`](SETUP.md) for everything the deploy script does under the hood. Edit identities at `src/agent_os/orchestrator/config/identities/*.yaml`.

---

## Cost what-to-expect

| | Monthly |
|---|---|
| Railway (5 services) | ~$40 |
| LLM API usage (light) | $5–50 |
| Tier 2 superagent VPSes | $4–6 each (only when spawned) |
| Outbound phone (Retell) | $0.05/min when calling |
| **Floor** | **~$45/mo** |
