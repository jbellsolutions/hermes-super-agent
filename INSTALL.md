# Install — One link, three power levels

Drop this file's master prompt into Claude Code, Codex, or Cursor and the agent walks you through every step. Or run the installer by hand. Both paths are below.

## Master prompt (paste into Claude Code / Codex / Cursor)

```
Set up Hermes for me, A to Z, from
https://github.com/jbellsolutions/hermes-super-agent.

Step 1 — Hermes prereq.
  Ask me: "Do you have Hermes installed already?"
  - If NO: walk me through QUICKSTART.md to install Hermes (uv sync,
    scripts/setup.sh). Confirm Hermes works locally before continuing.
  - If YES: skip to step 2.

Step 2 — Pick a power level.
  Ask me: "Saiyan, Kaioken, or Super Saiyan 5?"

  - Saiyan (lite, ~3 min, $0 infra):
    Keep my existing Hermes runtime. Drop the planner + 14 in-process
    runtimes + 16 skill files into my project. After install, run
    examples/saiyan_hello.py so I see it actually work.

  - Kaioken (local full, ~10 min, $0 infra, Docker required):
    Full Hermes super agent on my laptop. NATS + Temporal +
    Coordinator + Admiral all in Docker. Spawns Tier 2 superagents
    as sibling Docker containers on my machine. No Railway, no DO,
    no public URL. After install, run examples/kaioken_spawn_demo.py
    so I see 3 local agents fan out and report back.

  - Super Saiyan 5 (cloud, ~30 min, ~$45/mo floor + per-spawn):
    Full Railway control plane + DigitalOcean Tier 2 spawning.
    Always-on, public A2A endpoint, team-shared, real isolated VPS
    spawns. Walk me through every signup (Anthropic, Railway, DO,
    Telegram BotFather, @userinfobot) and write my .env. When deploy
    finishes, ask me to send "hello" to my Telegram bot.

Step 3 — Install.

  - Saiyan path:
      1. Verify python 3.11+ and git.
      2. Clone https://github.com/jbellsolutions/hermes-super-agent
         to /tmp/hermes-super-agent.
      3. Run:
           python3 /tmp/hermes-super-agent/install.py \
             --mode=saiyan --target=/path/to/my/project --yes
         If you can't find my project root, ask me.
      4. Stream the output. The installer copies the orchestrator,
         the 14 runtime adapters, the 16 SKILL.md files, merges
         saiyan deps into my pyproject.toml or requirements.txt,
         and runs a real smoke test against examples/saiyan_hello.py.
      5. After "saiyan install complete," run
           python examples/saiyan_hello.py --prompt "echo hello"
         and confirm it prints `hello`.
      6. Show me the wire-it-into-your-turn-handler snippet from the
         output so I see exactly where to plug it in.

  - Kaioken path:
      1. Verify Docker Desktop is running (`docker info`).
      2. Verify python 3.11+ and uv. Run `uv sync` in the repo.
      3. Make sure .env has ANTHROPIC_API_KEY at minimum.
      4. Run:
           python3 install.py --mode=kaioken --yes
         The installer brings up NATS, Temporal, Coordinator, and
         Admiral as Docker containers (~10 min for the first build).
      5. After healthchecks pass, run
           uv run python examples/kaioken_spawn_demo.py
         and confirm 3 superagent containers spawn, fan out, and
         tear down cleanly.
      6. Tell me about ./scripts/kaioken-down.sh for tear-down and
         ./scripts/kaioken-up.sh --telegram for the bot sidecar.

  - Super Saiyan 5 path:
      1. Walk me through every signup with URL and click instructions:
         Anthropic API key, Railway API token, Telegram bot token
         (BotFather), Telegram chat ID (@userinfobot). Then ask once
         whether I want any of: DigitalOcean (Tier 2 spawning), Retell
         AI (phone), Instantly.ai (cold email), Moonshot (Kimi K2.6),
         AgentOps (dashboards). Skip what I don't want.
      2. Write everything to .env at the repo root.
      3. Run: python3 install.py --mode=super-saiyan-5
         (wraps scripts/setup.sh + scripts/deploy.sh).
      4. Stream the output. Builds finish in the background on Railway.
      5. When deploy finishes, ask me to send "hello" to my Telegram
         bot. If it doesn't reply, check Admiral logs on Railway and
         walk me through the fix.

Don't write code. I'll paste keys. If anything fails, walk me through
the fix.
```

That's the natural-language single-link install. Paste it, agent does the rest.

---

## Manual fallback — run the installer yourself

### Saiyan (lite — drop into your existing Hermes)

You need: `python 3.11+`, `git`. Your existing project has an `agent_os/` or `src/agent_os/` directory.

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent /tmp/hermes-super-agent
python3 /tmp/hermes-super-agent/install.py --mode=saiyan \
    --target=/path/to/your/project --yes
```

What it does:

- Copies `agent_os/orchestrator/` (planner + adapters + config + identities), `agent_os/runtimes/` (14 in-process runtimes), and `vault/skills/active/tools/` (16 SKILL.md files) into your project
- Drops `examples/saiyan_hello.py` so you have a working demo
- Wires `saiyan_overrides.apply()` into the copied `adapters/__init__.py` — at import time, that strips fabric runtimes (coordinator, vps_spawn, local_spawn, etc.) from the registry and rewrites the "unknown runtime" error to point at the upgrade path
- Merges `pyyaml>=6.0` + `httpx>=0.27` into your `pyproject.toml` or `requirements.txt`, and offers to `uv sync` / `pip install` immediately
- Runs `examples/saiyan_hello.py --prompt "echo hello-from-saiyan-install"` end-to-end and asserts the output round-trips through the orchestrator
- Stamps every file with `# saiyan-installed: hermes-super-agent@<git-sha> on <date>` so `--check`, `--update`, and `--uninstall` know what's ours

After install, wire into your turn handler:

```python
from agent_os.orchestrator import intent_classifier
from agent_os.orchestrator.adapters.job_router import Job, dispatch
from agent_os.orchestrator.tool_planner import plan
from agent_os.orchestrator.plan_card import render

intent = intent_classifier.classify(user_text)
job = Job(prompt=user_text, tags=set(intent.tags))
tool_plan = plan(job, identity="primary_hermes")
print(render(tool_plan))               # show plan card
result = await dispatch(job, plan=tool_plan)
```

Manage the install over time:

```bash
python3 install.py --mode=saiyan --target=PATH --check       # drift report
python3 install.py --mode=saiyan --target=PATH --update      # refresh from upstream
python3 install.py --mode=saiyan --target=PATH --uninstall   # remove everything
python3 install.py --mode=saiyan --identities=coo,gtm-cmo    # pick identity packs
```

### Kaioken (local full — Docker on your laptop)

You need: `docker`, `python 3.11+`, `uv`. Anthropic API key in `.env` (others optional).

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
cp .env.example .env
# edit .env, add ANTHROPIC_API_KEY=sk-...
python3 install.py --mode=kaioken --yes
```

The installer:

1. Verifies `docker info` works
2. Optionally runs `scripts/setup.sh` to scaffold `.env` (only asks for Anthropic key + optional Telegram)
3. Calls `scripts/kaioken-up.sh` which runs `docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.kaioken.yml up -d` and waits for healthchecks
4. Brings up: `hermes-nats`, `hermes-temporal`, `hermes-coordinator`, `hermes-admiral`

Verify with the spawn demo:

```bash
uv run python examples/kaioken_spawn_demo.py
# → spawns 3 hermes-superagent-* sibling containers, waits for their
#   /agentCard to respond, prints results, tears them down
```

Tear down:

```bash
./scripts/kaioken-down.sh              # stop, keep volumes
./scripts/kaioken-down.sh --purge      # nuke volumes too
./scripts/kaioken-down.sh --kill-spawns  # also stop any leftover spawned superagents
```

### Super Saiyan 5 (cloud — Railway + DO)

You need: Railway, Anthropic, Telegram. Optional but recommended: DigitalOcean, Retell, Instantly, AgentOps.

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
python3 install.py --mode=super-saiyan-5
# (or directly: ./scripts/setup.sh && ./scripts/deploy.sh)
```

Five Railway services come up: NATS → Temporal → Coordinator → Archon → Admiral. ~30 min start to finish. After it's green, send `hello` to your Telegram bot and you're live with a public A2A endpoint, always-on, team-shareable.

---

## Installer reference

```
python3 install.py --mode=saiyan           [--target=PATH] [--dry-run] [--force]
                                           [--yes] [--check] [--update] [--uninstall]
                                           [--identities=primary_hermes,coo,...]
python3 install.py --mode=kaioken          [--yes] [--telegram]
python3 install.py --mode=super-saiyan-5
```

| Mode | Alias | What it does |
|---|---|---|
| `--mode=saiyan` | `--mode=lite` | Lite drop-in. Copies skills + planner + 14 runtimes into the target. |
| `--mode=kaioken` | — | Local Docker fabric. NATS + Temporal + Coordinator + Admiral as containers; spawns Tier 2 agents as sibling containers. |
| `--mode=super-saiyan-5` | `--mode=full`, `--mode=super-saiyan` | Full Railway + DigitalOcean cloud deploy. |

| Flag | Modes | What it does |
|---|---|---|
| `--target=PATH` | saiyan | Project root to install into. Default: cwd. |
| `--dry-run` | saiyan | Print every file that would change. Write nothing. |
| `--force` | saiyan | Overwrite user-modified files (otherwise they're preserved). |
| `--yes` | all | Skip confirmation prompts (pip install, .env scaffold, uninstall). |
| `--check` | saiyan | Report drift between installed copies and upstream. |
| `--update` | saiyan | Refresh stamped files from upstream. |
| `--uninstall` | saiyan | Remove every stamped file (with confirmation). |
| `--identities=...` | saiyan | Comma-separated identity packs. `list` to enumerate, `all` for everything. |
| `--telegram` | kaioken | Also start the Telegram bot sidecar (long-poll, no public URL needed). |

The installer is idempotent. Re-running updates only what changed. Dep merges deduplicate.

---

## Upgrade path

```
Saiyan  ──►  Kaioken  ──►  Super Saiyan 5
 ($0)        ($0 infra)     (~$45/mo + per-spawn)
```

You can jump directly. Saiyan → SS5 is just a fresh clone and `install.py --mode=super-saiyan-5` — the saiyan files in your project keep working, they just get joined by the Railway fabric. Saiyan → Kaioken is the same: clone the repo separately, bring up Docker, point your saiyan project at the Kaioken Admiral's A2A endpoint via env var.

See [docs/modes.md](docs/modes.md) for the deep-dive on what each mode contains and when to pick which.
