# Install — One link, two modes

Drop this whole file's master prompt into Claude Code, Codex, or Cursor and the agent walks you through every step. Or run the installer by hand. Both paths are below.

## Master prompt (paste into Claude Code / Codex / Cursor)

```
Set up Hermes for me, A to Z, from
https://github.com/jbellsolutions/hermes-super-agent.

Step 1 — Hermes prereq.
  Ask me: "Do you have Hermes installed already?"
  - If NO: walk me through QUICKSTART.md to install Hermes (uv sync,
    scripts/setup.sh, scripts/deploy.sh on Railway). Confirm Hermes
    responds on Telegram before continuing. Then go to step 2.
  - If YES: skip to step 2.

Step 2 — Pick a mode.
  Ask me: "Saiyan or super-saiyan?"
  - Saiyan (lite): keep my existing Hermes runtime; install just the
    planner + tier gates + 14 in-process runtimes + 16 SKILL.md files
    into my project. No new infrastructure. ~3 minutes.
  - Super-saiyan (full): bring up the full Railway fabric — NATS +
    Temporal + Coordinator + Archon + Admiral. Provisions Tier 2
    superagent VPSes on demand. ~30 minutes start to finish.

Step 3 — Install.
  - Saiyan path:
      1. Verify python 3.11+ and git are installed.
      2. Clone https://github.com/jbellsolutions/hermes-super-agent
         to /tmp/hermes-super-agent.
      3. Run: python3 /tmp/hermes-super-agent/install.py
                --mode=saiyan --target=/path/to/my/project
         If you can't find my project root, ask me.
      4. Stream the output. The script copies the orchestrator code,
         the 14 runtime adapters, the 16 SKILL.md files, and merges
         saiyan deps into my pyproject.toml or requirements.txt.
      5. After the script prints "saiyan install complete," run the
         smoke-test command it printed. Confirm it says
         "OK primary_tool=... tier=...".
      6. Show me the 5-line "from agent_os.orchestrator..." example
         from the output so I see exactly where to wire it into my
         Hermes turn handler.

  - Super-saiyan path:
      1. Walk me through every signup with the URL and what to click
         for each: Anthropic API key, Railway API token, Telegram bot
         token (BotFather), Telegram chat ID (@userinfobot). Then ask
         once whether I want any of: DigitalOcean (Tier 2 spawning),
         Retell AI (phone), Instantly.ai (cold email), Moonshot
         (Kimi K2.6), AgentOps (dashboards). Skip what I don't want.
      2. Write everything to .env at the repo root by running
         scripts/setup.sh non-interactively (it accepts piped input)
         or by editing .env directly.
      3. Run: python3 install.py --mode=super-saiyan
         (this is a thin wrapper that runs scripts/setup.sh +
         scripts/deploy.sh).
      4. Stream the output. Builds finish in the background on Railway.
      5. When deploy finishes, ask me to send "hello" to my Telegram
         bot and confirm it replies. If it doesn't, check Admiral
         logs at railway.app/dashboard and walk me through the fix.

Don't write code. I'll paste keys. If anything fails, walk me through
the fix.
```

That's the natural-language single-link install. Paste it, agent does the rest.

**Prefer a runnable wizard?** `scripts/launch.py` is the twin of this master
prompt — same flow, same wording. It asks Saiyan vs Super Saiyan first, runs
the Hermes preflight, walks you through keys and channels, then runs the
mode-aware installer:

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
./scripts/launch.py            # asks the mode, then walks the rest
./scripts/launch.py --mode=saiyan        # skip the mode question
```

---

## Manual fallback — if you'd rather just run the installer yourself

### Saiyan mode (lite — drop into your existing Hermes)

You need: `python 3.11+`, `git`. Your existing Hermes/Python project lives somewhere with an `agent_os/` or `src/agent_os/` directory.

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent /tmp/hermes-super-agent
python3 /tmp/hermes-super-agent/install.py --mode=saiyan --target=/path/to/your/project
```

The script copies:

- `agent_os/orchestrator/` — 7 planner modules + `adapters/` + `config/` (models, tiers, identities)
- `agent_os/runtimes/` — `_base.py` + 14 in-process runtimes (agent_zero, aider, browser_use, claude_managed, claude_subagents, codex_cli, computer_use, e2b, exa, hermes_self, livekit, openclaw, openswarm, terminal)
- `vault/skills/active/tools/` — 16 SKILL.md files

It also patches the copied `adapters/job_router.py` so `dispatch()` raises a friendly `RuntimeError` if you ask for a fabric-only runtime, and merges `pyyaml>=6.0` + `httpx>=0.27` into your `pyproject.toml` or `requirements.txt`.

Then install your project's deps the way you normally do (`pip install -r requirements.txt` or `uv sync`) and you're ready.

**Wire it into your Hermes turn handler in 5 lines:**

```python
from agent_os.orchestrator import intent_classifier
from agent_os.orchestrator.adapters.job_router import Job, dispatch
from agent_os.orchestrator.tool_planner import plan
from agent_os.orchestrator.plan_card import render

intent = intent_classifier.classify(user_text)
job = Job(prompt=user_text, tags=set(intent.tags))
tool_plan = plan(job, identity="primary_hermes")
print(render(tool_plan))               # show plan card to the user
# ... await user yes / YES / cancel ...
result = await dispatch(job, plan=tool_plan)
```

### Super-saiyan mode (full — Railway fabric)

You need: `git`, `python 3.11+`, `uv`, plus the Railway, Anthropic, and Telegram accounts listed in [QUICKSTART.md](QUICKSTART.md).

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent
cd hermes-super-agent
uv sync
python3 install.py --mode=super-saiyan
# (or directly: ./scripts/setup.sh && ./scripts/deploy.sh)
```

Five Railway services come up: NATS → Temporal → Coordinator → Archon → Admiral. ~30 minutes start to finish. After it's green, send `hello` to your Telegram bot and you're live.

---

## Installer reference

```
python3 install.py --mode=saiyan       [--target=PATH] [--dry-run] [--force]
python3 install.py --mode=super-saiyan
python3 install.py --mode=lite                  # alias for saiyan
python3 install.py --mode=full                  # alias for super-saiyan
```

| Flag | What it does |
|---|---|
| `--mode=saiyan\|lite` | Lite drop-in install. Copies skills + planner + 14 runtimes into the target. |
| `--mode=super-saiyan\|full` | Runs `scripts/setup.sh` + `scripts/deploy.sh` (full Railway deploy). |
| `--target=PATH` | Project root for saiyan mode. Default: current directory. |
| `--dry-run` | Print every file that would be created/updated. Write nothing. |
| `--force` | Overwrite existing target files. Off by default — protects your work. |

The installer is idempotent. Re-running with the same target updates files only if they've changed. Dep merges deduplicate — running twice doesn't double-append to your `requirements.txt`.

## What if I want to upgrade saiyan → super-saiyan later?

You don't need to uninstall saiyan. Clone `hermes-super-agent` fresh, `python3 install.py --mode=super-saiyan`, point your existing Hermes at the new Admiral's A2A endpoint. The skills layer you installed locally keeps working — it just gets joined by the fabric layer running on Railway.

See [docs/modes.md](docs/modes.md) for the full deep-dive on what each mode contains and the upgrade path.
