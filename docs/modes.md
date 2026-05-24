# Modes — Saiyan, Kaioken, Super Saiyan 5

Three install modes, one repo, one share link. This doc explains what's in each mode, when to pick which, and how to upgrade.

## TL;DR

|                       | **Saiyan (lite)**            | **Kaioken (local full)**             | **Super Saiyan 5 (cloud)**                   |
|-----------------------|------------------------------|--------------------------------------|----------------------------------------------|
| For                   | You already run Hermes; you want the brain | You want the full fleet on your laptop | You want always-on, team-shared, public-reachable |
| Where it runs         | Inside your existing project | Docker on your laptop                | Railway control plane + DigitalOcean spawns |
| Cloud accounts needed | None                         | None                                 | Anthropic + Railway + DO + Telegram + optional |
| Cost / month          | $0 infra                     | $0 infra                             | ~$45 floor + ~$24/mo per Tier 2 VPS          |
| Install time          | ~3 min                       | ~10 min (mostly Docker pull)         | ~30 min (signups + DNS + first deploy)       |
| Survives laptop sleep | n/a                          | No                                   | Yes                                          |
| Internet-reachable    | No                           | No (localhost only)                  | Yes — public HTTPS + webhook URL             |
| Tier 2 spawn target   | n/a                          | Local Docker container               | DigitalOcean droplet (~$24/mo)               |
| Upgrade path          | → Kaioken or → SS5           | → SS5 (same compose, different host) | terminal — this is the full form             |

When in doubt: **start Saiyan**. Free, 3 minutes, easy to upgrade. Step up to Kaioken when you want to actually spawn superagents. Step up to SS5 when you want them to outlive your laptop.

---

## Saiyan (lite)

**What you get:** the planner + 14 in-process runtimes + 16 skill files dropped into your existing project. Your code, your turn handler, our brain.

**What ships:**

- `agent_os/orchestrator/` — `tool_planner.py`, `model_planner.py`, `intent_classifier.py`, `tier_classifier.py`, `plan_card.py`, `catalog.py`, plus `adapters/` (job_router, plan_overrides, vault_memory, saiyan_overrides)
- `agent_os/orchestrator/config/` — `models.yaml`, `tiers.yaml`, plus selected `identities/*.yaml` (default `primary_hermes`; use `--identities=coo,gtm-cmo` to add more)
- `agent_os/runtimes/` — `_base.py` + 14 runtimes: `agent_zero`, `aider`, `browser_use`, `claude_managed`, `claude_subagents`, `codex_cli`, `computer_use`, `e2b`, `exa`, `hermes_self`, `livekit`, `openclaw`, `openswarm`, `terminal`
- `vault/skills/active/tools/` — 16 SKILL.md files (the 14 above + `composio.md` and `_catalog.md`)
- `examples/saiyan_hello.py` — 80-line working demo, uses only the `terminal` runtime (no API keys needed)

**What's deliberately NOT shipped:** the fabric. No NATS bus, no Temporal workflows, no Coordinator, no spawning. The copied `saiyan_overrides.apply()` strips those from the runtime registry at import time, and dispatch raises a friendly error pointing at Kaioken / SS5 if you ask for one.

**Use it for:** layering planning, model selection, and tier gating onto an agent you've already built. Or as a starting point for a custom Hermes-style stack without committing to the cloud fabric.

**Install:**

```bash
python3 install.py --mode=saiyan --target=/path/to/your/project --yes
```

**Manage:**

```bash
python3 install.py --mode=saiyan --target=PATH --check       # drift report
python3 install.py --mode=saiyan --target=PATH --update      # refresh from upstream
python3 install.py --mode=saiyan --target=PATH --uninstall   # remove everything
python3 install.py --mode=saiyan --identities=list           # enumerate identities
```

**Limits:**

- No Tier 2 spawning (asking for `spawn-superagent` raises a friendly RuntimeError)
- No NATS event stream — anything that publishes events will no-op
- No Temporal durability — long-running fan-outs are best-effort within your process

---

## Kaioken (local full)

**What you get:** every capability Super Saiyan 5 has, running entirely on your laptop. NATS + Temporal + Coordinator + Admiral in Docker. Tier 2 spawns become sibling Docker containers instead of cloud VPSes.

**What ships (in addition to everything in Saiyan):**

- `deploy/compose/docker-compose.kaioken.yml` — extends the base compose with the **admiral** service (built from root `Dockerfile`) and an optional **telegram-bot** sidecar (long-poll mode — no public URL needed)
- `src/agent_os/runtimes/local_spawn/` — the new runtime that talks to your laptop's Docker daemon via the SDK
- `src/agent_os/orchestrator/local_spawner.py` — Docker-API counterpart to `spawner.py`. Builds the `hermes-superagent:latest` image on first use, spawns containers on the `hermes-fabric` network, waits for `/agentCard` to respond, registers in `vault/projects/registry.yaml`
- `scripts/kaioken-up.sh`, `scripts/kaioken-down.sh` — one-command bring-up + tear-down
- `examples/kaioken_spawn_demo.py` — end-to-end proof: spawn 3 superagents, fan out, tear down

**How spawning differs:** the router checks `HERMES_MODE=kaioken` and routes `spawn-superagent` → `local_spawn` (instead of `vps_spawn`). Same A2A contract on both ends: parent Admiral gets back an agent card and an A2A URL. Doesn't matter whether the child is `http://hermes-superagent-xxx:8080` on the bridge network or `http://138.197.x.y:8080` on a droplet.

**Use it for:** real Tier 2 spawning without cloud spend. Testing fan-out patterns. Demos. Personal use where you don't need always-on. Air-gapped or compliance environments.

**Install:**

```bash
python3 install.py --mode=kaioken --yes              # standard bring-up
python3 install.py --mode=kaioken --yes --telegram   # also start Telegram bot
```

**Verify:**

```bash
uv run python examples/kaioken_spawn_demo.py
# spawns 3 superagents on the local fabric, waits for healthy, tears down
```

**Resource budget:** ~800MB RAM idle (NATS 50MB, Temporal 400MB, Coordinator 150MB, Admiral 200MB). Each spawned superagent ≈ 200MB. On a 16GB laptop you can comfortably run the fabric + ~30 spawns.

**Limits:**

- Laptop closed = fabric stops. No background work, no scheduled jobs.
- No public URL. Inbound webhooks (Retell, Telegram webhook mode, Instantly callbacks) don't work — but Telegram long-poll is fine because it's outbound.
- Spawned superagents share your laptop's resources. If Admiral crashes, children crash with it.
- Outbound traffic goes through your home/coffee-shop IP. Bad for email deliverability and risky for any provider that fingerprints residential IPs.

**Can I expose Kaioken via ngrok?** Yes for testing — `ngrok http 8080` and Admiral's A2A endpoint is reachable. But for anything ongoing, that's what Super Saiyan 5 is for.

---

## Super Saiyan 5 (cloud)

**What you get:** the full Hermes fleet, in the cloud, always-on, public, team-shared.

**What ships (in addition to everything in Kaioken):**

- `deploy/railway.toml`, `deploy/compose/docker-compose.yml` deployed to Railway
- 5 Railway services: NATS → Temporal → Coordinator → Archon → Admiral
- `src/agent_os/orchestrator/vps_provisioner.py` configured for DigitalOcean (or Hetzner — set `VPS_PROVIDER=hetzner`)
- `src/agent_os/orchestrator/bootstrap.py` SSH-bootstraps new Tier 2 VPSes
- Public A2A endpoint (Railway gives you `https://<your-app>.up.railway.app/agentCard`)

### The 10 reasons to choose SS5 over Kaioken

1. **Always-on.** Cron jobs survive laptop sleep, OS updates, travel. The agent can wake at 3am to scrape competitor pricing and have a brief in your inbox by 7am.
2. **Internet-reachable.** Public HTTPS means: Retell can call your A2A webhook for voice-channel turns; Instantly can post reply events back; Telegram can use webhook mode (lower latency than long-poll); other agents on the open agent web can discover your `/agentCard` and delegate work to you.
3. **Team-shared.** Cofounder, ops hire, CoS all hit the same Admiral. Identity packs route by sender (your Telegram ID → COO identity; partner's → CMO identity).
4. **Real Tier 2 spawning.** When the planner decides "this is a 6-hour job that needs its own VPS so it doesn't choke the main Admiral," SS5 provisions an actual isolated droplet. Spawns survive Admiral restarts and live independently until their TTL expires. Kaioken's local containers share laptop resources — Admiral crashes, they crash too.
5. **Dedicated outbound IP.** DO droplets get static IPs. Warm one for cold-email sending reputation (Instantly), or allow-list it for outbound calls (Retell PSTN trunk). Kaioken outbound looks residential — terrible for deliverability.
6. **Geographic placement.** Deploy in the region closest to the team (us-east, eu-west, etc.) for lowest user-facing latency. Tier 2 spawns can also be placed regionally — a scrape job targeting EU sites gets a Frankfurt droplet.
7. **Compute headroom.** Railway services can be sized up (2GB, 8GB, 16GB) without touching your laptop. Run 200 concurrent Tier 1 jobs without sweating local CPU.
8. **Isolated blast radius.** A bug in a runtime (or a malicious tool call from a hijacked prompt) is contained inside a Railway service / DO droplet, not running as your local user. SS5 keeps your dev machine safe.
9. **Observability story.** AgentOps + Datadog + Sentry plugged into a stable hostname. Aggregated metrics across all spawns. Kaioken can do the same but only while the laptop is open.
10. **Survivable.** Laptop dies? SS5 doesn't care. The Admiral's state (Temporal workflows, NATS streams, vault) is in the cloud. Replacing the laptop = `git clone && uv sync` = back at full power.

**Install:**

```bash
python3 install.py --mode=super-saiyan-5
# or directly:
./scripts/setup.sh && ./scripts/deploy.sh
```

**Cost floor (typical):** Railway ~$25/mo (5 small services), Temporal Cloud or self-hosted Temporal on Railway ~$10-20/mo, plus ~$24/mo per active Tier 2 VPS. Anthropic / model API usage on top.

---

## Upgrade paths

### Saiyan → Kaioken

Saiyan installed in your existing project? Bring up Kaioken alongside:

```bash
# In a separate clone of hermes-super-agent
python3 install.py --mode=kaioken --yes
```

Then point your saiyan project at the Kaioken Admiral via env var:

```bash
HERMES_ADMIRAL_A2A=http://localhost:8080
```

Your saiyan planner can now delegate spawn jobs to the Kaioken Admiral instead of raising the friendly RuntimeError.

### Saiyan → Super Saiyan 5

Same idea, point at the Railway URL:

```bash
HERMES_ADMIRAL_A2A=https://your-app.up.railway.app
```

### Kaioken → Super Saiyan 5

Same compose file pattern, different host. Take your tested local `.env`, push the relevant keys to Railway, run `./scripts/deploy.sh`. Local Kaioken stays up for dev; production traffic moves to the cloud.

---

## FAQ

**Why is Saiyan called "Saiyan" and not "lite"?**

Because the names describe the actual difference: base form, powered-up form, ultimate form. `lite`, `full`, `super-saiyan` all work as aliases — the installer accepts both spellings.

**Does Kaioken survive a reboot?**

The containers restart automatically (the compose file sets `restart: unless-stopped`), so yes, once you've brought it up once it'll come back after a reboot — *if* Docker Desktop is set to start on login. Laptop sleep is different: the containers pause and resume.

**Can I run Kaioken on a Raspberry Pi / cheap VPS?**

Probably yes for the fabric (NATS + Coordinator + Admiral fit in ~500MB), but Temporal alone wants ~400MB. A 2GB Pi 4 works for the fabric; spawning superagents needs more headroom.

**Can I mix modes — Saiyan in my main app, Kaioken running on the side for spawns?**

Yes. Wire your Saiyan app to use Kaioken's Admiral as a delegation target via A2A. Your local planner picks tools; when it picks `spawn-superagent`, it sends the job to Kaioken's Admiral which actually spawns.

**Where does Kaioken's `hermes-superagent:latest` image come from?**

It's built from the root `Dockerfile` (the same image Railway uses for the Admiral in SS5). The first spawn pays a ~30s build cost; subsequent spawns are instant. `./scripts/kaioken-up.sh --rebuild` forces a rebuild.

**Is there a "Super Saiyan God" mode for the recursive fleet?**

Not yet. The naming hook is there for when Hermes spawns Hermeses that spawn their own Hermeses — the recursive multi-agent fleet. For now, Tier 2 superagents can spawn Tier 1 specialists, but they don't recurse into more Tier 2s. That's the next round.
