---
name: agent-os
description: Drive the conversational launch of agent-os, OR orient yourself in an existing repo. Detects which mode based on whether the repo has been bootstrapped.
---

## Mode detection

Run this check first:

```bash
test -f .env && test -d .venv && echo "bootstrapped" || echo "fresh"
```

- **fresh** → run **Launch Mode** (below).
- **bootstrapped** → run **Operating Mode** (further down).

---

## Launch Mode (fresh repo, drop-the-link flow)

The user just dropped this repo's URL into your session. You are the conversational installer. Your job: walk them through `LAUNCH.md` Path A in plain English. Don't dump documentation at them — converse.

### Step 1 — Confirm scope

Ask the user, in one short message, the minimum setup questions:

1. *Which commercial tier?* Operator / Pro Operator / Enterprise.
2. *What business/project/offer is this for?* Include first 3 workflows the agent should own.
3. *Which channels do they want active first?* Slack? Telegram? Web text? Web voice? Any combination.
4. *Which model should Hermes default to?* Default suggestion: `claude-opus-4-7` unless they want OpenAI/OpenRouter.
5. *Where do they want to deploy?* Local-only / Railway / DigitalOcean VPS / Docker Compose / Fly.io.

Example phrasing:

> *"I'll walk you through Super Agent setup like a commercial onboarding — should take 15–30 minutes depending on keys. Quick setup questions: (1) tier: Operator, Pro Operator, or Enterprise? (2) what business/project is this for and what first 3 workflows should the agent own? (3) channels: Slack, Telegram, web chat, voice, or a mix? (4) default model/provider? (5) deploy target: local, Railway, DigitalOcean/VPS, Docker Compose, or Fly?"*

Use `AskUserQuestion` if you have it; otherwise plain prose.

### Step 2 — Collect keys

Based on their channel choices, ask for ONLY the keys actually needed. Don't ask for everything in `.env.example` if they only picked Slack. Reference `.env.example` for the canonical list.

Required regardless of channel: `ANTHROPIC_API_KEY` (or whichever provider their default model needs).

Business setup fields: `SUPER_AGENT_TIER`, `BUSINESS_NAME`, `BUSINESS_TYPE`, `FIRST_WORKFLOWS`, `HUMAN_APPROVAL_REQUIRED`.

If they picked Slack: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`. Link them to https://api.slack.com/apps if they don't have an app yet.

If Telegram: `TELEGRAM_BOT_TOKEN`. Link to @BotFather.

If web voice: `LIVEKIT_*` triple, plus voice provider key (`OPENAI_API_KEY` or `GEMINI_API_KEY`).

If Enterprise and deployment discovery is requested: `RAILWAY_TOKEN` and/or `DIGITALOCEAN_ACCESS_TOKEN`. If the user asks about Orgo/managed cloud computers, explain it is optional and only collect `ORGO_API_KEY` when the customer/workspace needs an isolated visible desktop.

For each key the user doesn't have, ASK if they want to skip it (and disable that channel/runtime for now) or pause to grab it. Do not block.

### Step 3 — Stage `.env`

Once keys are collected, write them to `.env`:

```bash
cp .env.example .env
# then edit with the values gathered above
```

Use the `Edit` tool to fill in each value the user provided. Leave the rest blank (they're optional).

### Step 4 — Bootstrap

Run, in order:

```bash
./scripts/bootstrap.sh        # installs uv if missing, syncs Python, installs pnpm
uv run pytest -q              # 23 tests should pass
uv run agent-os manifest      # builds the system graph; writes vault/graph/system.yaml
```

After each, summarize the result for the user in one line. If something fails, debug interactively — most likely a missing dep or a key that didn't make it into `.env`.

### Step 5 — Boot Hermes

```bash
uv run agent-os boot
```

This is currently a stub (Stage 2 of `docs/EXECUTION-PLAN.md`). It returns a JSON describing the boot intent. **Tell the user this honestly.** The skeleton is here; the real Hermes wiring is the next session's job.

If they want to proceed with the Hermes wiring NOW, offer to drop into Stage 2 — that's a focused 1–2 hour session where you wire `vendor/hermes-agent` into `src/agent_os/orchestrator/boot.py` for real.

### Step 6 — Verify single-state (when channels are live)

Once at least two channels are wired (post Stage 7 of the execution plan), run:

```bash
uv run pytest tests/integration/test_single_state_smoke.py
```

Confirm the test passes. This is the load-bearing acceptance criterion for the accessibility layer.

### Step 7 — Hand-off

Give the user a 5-line summary:

- What's running (channels, model, deploy target).
- Tier/business/workflows and approval rules.
- What's stubbed and which stage of `docs/EXECUTION-PLAN.md` lights it up.
- What the daily loops do (upgrader at 02:00, agi-audit at 02:30, heartbeat every 5 min).
- The three operating skills they have now (`/agent-os`, `/explain`, `/route`).
- A single concrete next move ("ship Stage 2 next session, then Stage 3 after").

---

## Operating Mode (bootstrapped repo, day-to-day)

Run `agent-os manifest` to refresh the system graph. Then:

1. Read [ARCHITECTURE.md](../../ARCHITECTURE.md) for the orchestrator/runtime model.
2. Read [ETHOS.md](../../ETHOS.md) for the unbreakable rules (don't edit `vendor/`, don't add a 15th framework).
3. Identify which package the work belongs to (`src/agent_os/orchestrator`, `src/agent_os/runtimes/<name>`, `src/agent_os/manifest`, `src/agent_os/quality`, `src/agent_os/upgrader`, `src/agent_os/channels`, `packages/webapp`, `packages/dashboard`).
4. Use `/route --tags ...` to confirm which runtime your work would dispatch to.

For commercial/multi-business decisions, read `docs/commercial-packaging.md` and `docs/portfolio-agent-architecture.md` before recommending another Hermes instance or a shared memory layout.

For Railway/DigitalOcean discovery, follow `runbooks/deployment-access.md`: read-only inventory first, no mutations without explicit approval.

If the work spans packages, write a short plan in `vault/decisions/<date>-<topic>.md` first.

For introspection ("what's running?", "who wrote this output?", "how does X connect to Y?"), use `/explain`.

---

## Hard rules (apply in both modes)

- **Never edit `vendor/`.** It breaks the upgrader. Open an upstream PR or wrap in `src/agent_os/runtimes/`.
- **Never start another framework wrapper.** New ideas go into a runtime adapter, a Hermes skill, or upstream.
- **Single-state guarantee.** Every channel writes through `vault_memory` — no per-channel state.
- **Smoke tests are non-negotiable for the upgrader.** A bad upstream commit silently promoted is the failure mode that takes the system down.
- **Default to Hermes.** Specialist runtimes are exceptions, not defaults.
- **Update setup instructions with every update.** If you add a tool, runtime, tier, deployment path, or workflow, update README/LAUNCH/setup docs in the same change.
- **Separate serious businesses.** One primary Hermes can orchestrate the portfolio, but project/customer agents need isolated vaults, secrets, deploy targets, and skills.
