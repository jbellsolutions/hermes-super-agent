# Mode B — Local Fabric Stack

Brings up NATS + Temporal + Coordinator as Docker containers on your laptop. The Admiral itself stays on the host as a Python process.

## Requirements

- Docker Desktop or `colima` + Docker CLI
- ~2GB free RAM, ~3GB free disk
- An `.env` at the repo root with at least `ANTHROPIC_API_KEY` set (other LLM keys optional)

## Start

```bash
cd hermes-super-agent
cp .env.example .env  # fill in ANTHROPIC_API_KEY (and any others you have)
cd deploy/compose
docker compose up -d --build
```

First boot takes ~3 minutes (Temporal pulls + Coordinator builds). Subsequent boots are seconds.

## Wire the Admiral to the local stack

Add these to your `.env`:

```bash
NATS_URL=nats://localhost:4222
TEMPORAL_HOST=localhost:7233
COORDINATOR_URL=http://localhost:8000
```

Now from the repo root:

```bash
uv run agent-os run \
    --prompt "research these 3 startups in parallel" \
    --tags fan-out \
    --meta sub_prompts="OpenAI||Anthropic||Mistral" \
    --meta coordinator_model=claude-sonnet-4-5 \
    --yes
```

You'll see real fan-out (3 actual LLM calls) and live progress events on NATS.

## Watch live events

```bash
docker exec hermes-nats nats sub 'agents.>'
```

## URLs while running

| Service | URL | Use |
|---|---|---|
| Coordinator | http://localhost:8000 | A2A endpoint |
| Coordinator agent card | http://localhost:8000/agentCard | Discovery |
| Temporal UI | http://localhost:8088 | Watch durable workflows |
| NATS monitoring | http://localhost:8222 | Server stats |

## Stop

```bash
docker compose down              # stop, keep data
docker compose down -v           # stop, wipe NATS + Temporal state
```

## Why containers and not native?

NATS and Temporal both have native installers, but `docker compose` gets you a single command that brings up the whole fabric in a known state. If you'd rather run them natively, point `NATS_URL` and `TEMPORAL_HOST` at your local installs — Hermes doesn't care where they live.
