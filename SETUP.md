# Hermes Fabric — Setup Runbook

> **Most people should run [`QUICKSTART.md`](QUICKSTART.md), not this.** Two scripts, ~30 minutes, done. This file is the long-form reference for what those scripts do under the hood and for power users who want to deploy services individually.

The default deploy is **Railway-managed** — every fabric service runs as its own Railway service, fully managed, ~$40/mo. Tier 2 spawned superagents land on DigitalOcean droplets because Railway containers don't support SSH bootstrap.

---

## Agent personas — giving each agent its own identity

Every agent in the fleet has a **persona**: a name, a role, a voice, and a list of tools it's allowed to use. Personas are defined in plain YAML files — no code changes needed to create or swap them.

### How it works

When an agent starts up, it reads its identity from an environment variable called `AGENT_IDENTITY`. That name maps to a file in `src/agent_os/orchestrator/config/identities/<name>.yaml`. The file contains a `system_prompt` that gets injected into every LLM call, so the agent always knows who it is, what it owns, and what tools it has access to.

Four personas ship out of the box:

| Name | Who they are |
|---|---|
| `supersan` | The Super Agent — the primary orchestrator. Owns everything, routes work to the right specialist. |
| `coo` | Alex, the COO — sees the whole org, delegates aggressively, holds everyone accountable. |
| `gtm` | Jordan, the GTM Agent — owns content, leads, and brand. Knows your CRM and email tools. |
| `head_of_ops` | Morgan, the Head of Operations — runs the client pipeline, watches the funnel, catches broken jobs. |

### Switching personas from Telegram

You don't need to redeploy to switch personas. In any Telegram conversation with Hermes:

- `/identity` — shows which persona is active and lists all available options
- `/identity coo` — switches to Alex for the rest of that conversation
- `/identity video_agent` — switches to any custom persona you've created

The persona you set is remembered for that chat session. Every message after the switch goes through that agent's system prompt, memory, and tool rules.

### Setting a default persona for a deployment

If you want a service to always start as a specific persona, set this in its environment:

```
AGENT_IDENTITY=coo
```

On Railway, set it under the service's Variables tab. On a VPS, add it to the `.env` file. On Docker, pass it with `-e AGENT_IDENTITY=coo`.

### Creating a new persona

1. Create a YAML file at `src/agent_os/orchestrator/config/identities/<name>.yaml`
2. Give it a `system_prompt` that describes who the agent is, what it owns, and how it should behave
3. Optionally add `tools_allowed`, `tools_denied`, and `default_tier_ceiling`
4. Commit and deploy — then send `/identity <name>` in Telegram to activate it

Example — a video production agent:

```yaml
name: Vex
title: Video Production Agent
system_prompt: |
  You are Vex, the video production agent. You own the full video pipeline:
  scripting, transcription, editing workflows, thumbnail generation, and
  publishing to YouTube and social. You have shell access and know ffmpeg.
  You remember every project we've worked on together.
tools_allowed:
  - hermes_self
  - terminal
  - exa
default_tier_ceiling: 2
```

The file name (without `.yaml`) is what you type after `/identity`. That's all there is to it.

---

## Why both Railway and DigitalOcean?

- **Railway** runs the **fixed always-on services** (NATS, Temporal, Coordinator, Archon wrapper, Admiral). One Dockerfile per service, auto-restart, public TLS URLs, env vars in a dashboard. You set it up once and forget.
- **DigitalOcean** runs **spawned Tier 2 superagents** — each spawn is a brand-new machine with its own SSH access, its own Hermes install, its own optional sub-fleet. Railway can't spawn full machines.

Railway gets used because the fleet's brain needs to be always-on with managed ops; DO gets used because spawned superagents need full-machine control. They serve different roles.

---

## Other deploy modes (advanced; skip unless you have a reason)

| Mode | Where things run | Cost/mo | Use when |
|---|---|---|---|
| A. Local dev | Admiral on laptop, fabric stubs | $0 | Trying out the CLI without deploying anything |
| B. Local Docker stack | Admiral on laptop, fabric in `docker compose` | $0 + LLM | Hacking on coordinator code; want full local fabric |
| B+. Single DO droplet | Everything on one droplet via `docker compose` | ~$12 + LLM | You'll do your own ops to save money |
| **C. Railway managed (default)** | Each fabric service is its own Railway service | ~$40 + LLM | Plug-and-play, always-on, zero ops |

---

> Code-side prerequisites (already done): commits b4b2e35 → bb46e06 on `hermes-super-agent`. The Coordinator and Archon wrapper both live as sub-deploys under `deploy/`.

---

## Step 1 — NATS JetStream on Railway (~10 min)

```bash
cd hermes-super-agent
railway login                                                # interactive
railway init --name hermes-fabric                            # one-time
railway add --service nats
railway up --service nats --config deploy/nats/railway.json
```

After deploy, in the Railway dashboard expose the service publicly (Settings → Networking → Generate Domain). Copy the TCP URL.

```bash
railway variables set NATS_URL="nats://<host>.railway.app:4222"
```

**Verify:**
```bash
uv run python -c "
from agent_os.bus.nats_publisher import publish_event
publish_event('test.smoke', {'ok': 1})
print('connected')
"
```

**Unlocks:** real-time fleet event bus.

---

## Step 2 — Temporal on Railway (~10 min)

```bash
railway add --service temporal
railway up --service temporal --config deploy/temporal/railway.json
```

Expose port 7233 (TCP). Copy the host.

```bash
railway variables set TEMPORAL_HOST="<host>.railway.app:7233"
```

**Verify:**
```bash
uv run python -c "
import asyncio
from temporalio.client import Client
asyncio.run(Client.connect('$TEMPORAL_HOST'))
print('connected')
"
```

**Unlocks:** durable fan-out (kill mid-run, restart resumes).

---

## Mode B+ — single DO droplet alternative (skip Steps 1–3, ~30 min total)

Instead of three separate Railway services for NATS / Temporal / Coordinator, run all three on a single $12/mo DigitalOcean droplet via `docker compose`. Admiral runs on the same droplet (or your laptop, your call).

```bash
# 1. Provision the droplet
doctl compute droplet create hermes-fabric \
    --image ubuntu-24-04-x64 --size s-1vcpu-2gb --region nyc3 \
    --ssh-keys $DO_SSH_KEY_FINGERPRINT --wait

# 2. SSH in and install Docker + clone the repo
ssh root@<droplet-ip> 'apt-get update && apt-get install -y docker.io docker-compose-plugin git && \
    git clone https://github.com/jbellsolutions/hermes-super-agent /opt/hermes && \
    cd /opt/hermes/deploy/compose && \
    cp /opt/hermes/.env.example /opt/hermes/.env'

# 3. Edit /opt/hermes/.env on the droplet — set ANTHROPIC_API_KEY etc
# 4. Start the stack
ssh root@<droplet-ip> 'cd /opt/hermes/deploy/compose && docker compose up -d --build'
```

Expose ports 4222 (NATS), 7233 (Temporal), 8000 (Coordinator) via your firewall, or keep them private and run Admiral on the same box.

**Verify:**
```bash
ssh root@<droplet-ip> 'docker compose ps'
# all three services should show "running"
```

**Cost:** ~$12/mo flat. **Trade-off:** you do the ops. Skip to Step 4 from here.

---

## Step 3 — Hermes Coordinator service (~15 min)

The coordinator lives at `deploy/coordinator/` in this repo as a self-contained Railway sub-deploy. Tests are green (6/6).

```bash
cd hermes-super-agent
railway add --service coordinator
railway up --service coordinator --root-directory deploy/coordinator
railway variables set --service coordinator \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    NATS_URL="nats://<host>.railway.app:4222" \
    COORDINATOR_DEFAULT_MODEL="claude-sonnet-4-5"
```

Expose port 8000 publicly. Copy the URL.

Back in `hermes-super-agent`:
```bash
railway variables set COORDINATOR_URL="https://<service>.railway.app"
```

**Verify:**
```bash
curl https://<service>.railway.app/agentCard | jq .name
# → "Hermes Coordinator"

uv run agent-os run \
    --prompt "research these 3 items" \
    --tags fan-out \
    --meta sub_prompts="A||B||C" \
    --meta coordinator_model=claude-sonnet-4-5 \
    --yes
# → 3 actual completed sub-results
```

**Unlocks:** N-agent fan-out with model-pluggable LLM and live NATS progress.

---

## Step 4 — COO Specialist channels (~30 min, mostly account setup)

### 4a — Retell AI (phone)
1. Sign up at https://retellai.com → API Keys → copy key.
2. Create an agent in their dashboard → copy agent ID.
3. Set:
   ```bash
   railway variables set RETELL_API_KEY=... RETELL_AGENT_ID=...
   ```

### 4b — Instantly.ai (cold email)
1. Sign up at https://instantly.ai → Settings → Integrations → API key.
2. Create a campaign (will be the default destination).
3. Set:
   ```bash
   railway variables set INSTANTLY_API_KEY=...
   ```

**Verify (use your own number/email — Tier 3 gate will require `--yes`):**
```bash
uv run agent-os run \
    --prompt "Hi, calling about Q3 plan" \
    --tags phone \
    --meta phone_number=+1XXXXXXXXXX \
    --yes

uv run agent-os run \
    --prompt "Quick intro about our service" \
    --tags email \
    --meta to_email=you@example.com \
    --meta campaign_id=<id> \
    --yes
```

**Unlocks:** outbound phone + email under Tier 3 explicit-YES gate.

---

## Step 5 — Archon agent builder (Tier 1 spawning) (~30 min)

The repo includes a thin A2A wrapper for Archon at `deploy/archon/`. It runs in stub mode until you wire it to a real Archon deployment.

```bash
cd deploy/archon
railway init --name archon-wrapper
railway up
```

Get the public URL.

In `hermes-super-agent`:
```bash
railway variables set \
    ARCHON_A2A_URL="https://<archon-wrapper>.railway.app" \
    RAILWAY_API_KEY="<from https://railway.app/account/tokens>"
```

**Verify (stub mode):**
```bash
curl $ARCHON_A2A_URL/agentCard | jq .name
# → "Archon Agent Builder"

uv run agent-os spawn --tier 1 --prompt "linkedin outreach specialist"
# → returns a stub AGENT.md until real Archon is wired
```

**Wire real Archon** by editing `deploy/archon/wrapper.py:_delegate_to_archon` to call your actual Archon `/api/generate` endpoint.

**Unlocks:** "create a specialist" jobs from Telegram.

---

## Step 6 — Tier 2 VPS spawning (DigitalOcean) (~15 min)

```bash
# On your laptop
brew install doctl                                            # if needed
doctl auth init                                               # paste DO API token
doctl compute ssh-key import hermes-fleet \
    --public-key-file ~/.ssh/id_rsa.pub
doctl compute ssh-key list --format Fingerprint --no-header
```

Copy the fingerprint, then on Railway (or wherever Admiral runs):
```bash
railway variables set \
    DO_API_TOKEN=... \
    DO_SSH_KEY_FINGERPRINT=<fingerprint> \
    SSH_PRIVATE_KEY_PATH=/app/.ssh/id_rsa
```

Mount your SSH private key as a Railway secret file at `/app/.ssh/id_rsa` (Railway dashboard → Variables → Secrets → File).

**Verify:**
```bash
uv run agent-os spawn --tier 2 --prompt "cold-email superagent"
# → DO droplet provisioned, Hermes booted, registered in registry.yaml within ~12 min
```

**Unlocks:** full superagent spawning with their own sub-fleets.

---

## Step 7 — Admiral always-on (~20 min)

So far the Admiral runs from your laptop via `agent-os run`. Make it always-on:

```bash
cd hermes-super-agent
railway add --service admiral
railway up --service admiral
railway variables set \
    ANTHROPIC_API_KEY=... \
    OPENAI_API_KEY=... \
    NATS_URL=... TEMPORAL_HOST=... COORDINATOR_URL=... \
    ARCHON_A2A_URL=... RAILWAY_API_KEY=... \
    DO_API_TOKEN=... DO_SSH_KEY_FINGERPRINT=... SSH_PRIVATE_KEY_PATH=/app/.ssh/id_rsa \
    RETELL_API_KEY=... RETELL_AGENT_ID=... INSTANTLY_API_KEY=... \
    TELEGRAM_BOT_TOKEN=<your bot> TELEGRAM_CHAT_ID=<your chat>
```

The Admiral subscribes to NATS `agents.>` on boot, exposes A2A on `/agentCard /messages /tasks/{id}`, and listens for Telegram messages.

**Unlocks:** "Hey Hermes, …" works from your phone.

---

## Step 8 — AgentOps (~5 min)

```bash
uv add agentops                                              # in hermes-super-agent
railway variables set AGENTOPS_API_KEY=<from app.agentops.ai>
git add pyproject.toml uv.lock && git commit -m "deps: agentops"
```

Already wired into `_cmd_run` and `_cmd_spawn`. Auto-instruments every LLM call.

**Unlocks:** unified cost / latency / error dashboard across all models.

---

## Step 9 — Run the verify gauntlet

The five plan-level acceptance tests:

| # | Test | How to run | Pass when |
|---|---|---|---|
| 1 | Real-time fleet view | `nats sub 'agents.>'` (any laptop with `nats` CLI) | Heartbeats from every service flow live; no polling |
| 2 | Crash recovery | Telegram: "fan out 50 research items"; mid-run, `railway down --service admiral` then `railway up` | Temporal resumes; final result has all 50 sub-tasks |
| 3 | Instant alerts | `nats pub agents.test.alert '{"needs_human":true}'` | Telegram receives alert within 30s |
| 4 | Tier 1 spawn | Telegram: "Create a LinkedIn specialist" | Live Railway service heartbeating in NATS in <15 min |
| 5 | Tier 2 spawn | Telegram: "Spin up a cold email superagent" | DO droplet + 3 sub-agents running in <15 min |

When all five pass, the fabric is shipping.

---

## Cost summary (recurring)

| Component | Mode B+ (single DO droplet) | Mode C (Railway managed) |
|---|---|---|
| NATS | included | ~$5 |
| Temporal | included | ~$15 |
| Coordinator | included | ~$5 |
| Archon wrapper | included | ~$5 |
| Admiral | included | ~$10 |
| Droplet (2GB) | ~$12 | n/a |
| **Fixed** | **~$12/mo** | **~$40/mo** |
| LLM usage | usage | usage |
| Retell phone | ~$0.05/min | same |
| Instantly | tier-based | same |
| Tier 2 superagent VPSes | $4–6 each | same |
| AgentOps | free tier | free tier |
