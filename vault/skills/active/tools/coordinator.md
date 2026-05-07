---
name: coordinator
runtime: coordinator
tier: 2
category: fan_out
cost_class: medium
risk_class: low
preferred_models: []
mcp_or_native: native
description: Delegate entire fan-out jobs to a deployed Coordinator A2A service that internally runs up to 300 parallel sub-agents. The model used by the coordinator is selectable per-job via job.metadata['coordinator_model'] or via COORDINATOR_DEFAULT_MODEL env var. Wrapped in a Temporal durable workflow so crash recovery is automatic.
---

## When to use
- Tasks that decompose into many parallel independent sub-tasks (research across 200 companies, batch processing, parallel analysis)
- Fan-out jobs where Hermes would need to manually spawn >5 sub-agents
- Any job tagged: `fan-out`, `coordinator`, `swarm-coordinator`, `parallel`, `batch`

## When NOT to use
- Simple single-model tasks → hermes_self
- Coding tasks → codex_cli / aider
- Browser automation → agent_zero / browser_use
- Small deliverables → openswarm
- Outbound phone/email → retell_channel

## How it works
1. Admiral routes job to `coordinator` runtime via A2A delegation
2. `src/agent_os/runtimes/coordinator/invoke.py` resolves which model to use:
   - `job.metadata['coordinator_model']` (per-job override) →
   - `COORDINATOR_DEFAULT_MODEL` env var →
   - whatever the coordinator service has configured locally (sent as "" in payload)
3. Sends the job to the Coordinator A2A endpoint with model in metadata
4. The coordinator service decomposes internally, fans out to N parallel sub-agents using the chosen model
5. Progress is published to NATS: `agents.coordinator.task.{task_id}`
6. The entire fan-out is wrapped in a Temporal `FanOutWorkflow` — kill Admiral mid-run, restart, Temporal resumes from the last activity

## Cost & latency
- Cost depends entirely on the model selected per-job
- Latency: 5-60 minutes depending on fan-out depth and chosen model
- Temporal workflow overhead: negligible

## Examples
- "Research the top 200 AI startups and produce a competitive landscape report"
  → `metadata: {coordinator_model: "claude-sonnet-4.7"}`
- "Fan out this list of 50 companies to 50 parallel research agents"
  → `metadata: {coordinator_model: "deepseek-v4-pro"}` (cheap)
- "Analyze all 300 customer support tickets and categorize them"
  → no metadata override → uses COORDINATOR_DEFAULT_MODEL

## Configuration
- `COORDINATOR_URL` — A2A endpoint for the deployed coordinator service
- `COORDINATOR_DEFAULT_MODEL` — fallback model id (e.g. `claude-sonnet-4.7`); empty → service default
- `TEMPORAL_HOST` — Temporal server endpoint (default: `localhost:7233`)

## Alternatives (ordered)
1. **openswarm** — for smaller multi-deliverable jobs (<10 parallel agents)
2. **hermes_self** — for tasks that don't need true fan-out
3. **claude_managed** — for long-running single-model cloud tasks

## See also
- src/agent_os/runtimes/coordinator/invoke.py
- src/agent_os/workflows/fan_out.py
- deploy/temporal/railway.json
