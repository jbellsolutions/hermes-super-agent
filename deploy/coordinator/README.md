# Hermes Coordinator (sub-deploy)

A2A-compliant fan-out coordinator for the Hermes fleet. Receives a job, decomposes it into N parallel sub-prompts, runs each on the LLM the caller specifies, and returns aggregated results.

This is a Railway sub-deploy of `hermes-super-agent`. Build context is this directory. The Admiral's client lives at `src/agent_os/runtimes/coordinator/invoke.py` — wire-format contract stays in sync because it's the same repo.

**Designed to be deployed once and pointed at by Hermes Admiral.** The model is selected per-job — no LLM lock-in.

## API (A2A protocol)

```
GET  /agentCard         → service description (auto-discovered by Admiral)
POST /messages          → submit a job, returns {taskId, state}
GET  /tasks/{task_id}   → poll for status + results
GET  /health            → uptime check
```

### Submit a fan-out job

```bash
curl -X POST $COORDINATOR_URL/messages \
  -H "Content-Type: application/json" \
  -d '{
    "parts": [{"kind": "text", "text": "Research these companies"}],
    "metadata": {
      "model": "claude-sonnet-4-5",
      "sub_prompts": "Research Acme||Research Globex||Research Initech",
      "concurrency": 10
    }
  }'
```

Returns `{"taskId": "...", "state": "submitted"}`.

### Poll for completion

```bash
curl $COORDINATOR_URL/tasks/<taskId>
```

Returns artifacts (one per sub-prompt) once `status.state == "completed"`.

## Supported models (auto-routed by id prefix)

| Prefix | Backend | Env var |
|---|---|---|
| `claude-*` | Anthropic | `ANTHROPIC_API_KEY` |
| `gpt-*`, `o1*`, `o3*` | OpenAI | `OPENAI_API_KEY` |
| `deepseek-*` | DeepSeek | `DEEPSEEK_API_KEY` |
| `kimi*`, `moonshot*` | Moonshot | `MOONSHOT_API_KEY` |
| `gemini*`, `google/*` | Google | `GOOGLE_API_KEY` |
| anything else | OpenRouter | `OPENROUTER_API_KEY` |

## Deploy to Railway

From the repo root:

```bash
railway add --service coordinator
railway up --service coordinator --root-directory deploy/coordinator
railway variables set --service coordinator \
  ANTHROPIC_API_KEY=sk-... \
  COORDINATOR_DEFAULT_MODEL=claude-sonnet-4-5 \
  NATS_URL=nats://your-nats.railway.app:4222
```

Then on the Hermes Admiral service:

```bash
railway variables set --service admiral COORDINATOR_URL=https://your-coordinator.railway.app
```

## Run locally

```bash
cd deploy/coordinator
uv sync
cp .env.example .env  # fill in keys
uv run hermes-coordinator
```

## NATS events (optional)

If `NATS_URL` is set, the coordinator publishes live progress to:

```
agents.coordinator.task.{task_id}.started
agents.coordinator.task.{task_id}.progress    (per sub-task)
agents.coordinator.task.{task_id}.completed
agents.coordinator.task.{task_id}.failed
```

Admiral subscribes to `agents.>` and renders these in real-time fleet view.
