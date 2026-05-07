---
name: kimi_coordinator
runtime: kimi_coordinator
tier: 2
category: fan_out
cost_class: medium
risk_class: low
preferred_models: [kimi-k2-coordinator]
mcp_or_native: native
description: Delegate entire fan-out jobs to the Kimi K2.6 Swarm Coordinator — a deployed service that internally runs up to 300 parallel sub-agents coordinating 4,000 steps via the Moonshot API. Wrapped in a Temporal durable workflow so crash recovery is automatic.
---

## When to use
- Tasks that decompose into many parallel independent sub-tasks (research across 200 companies, batch processing, parallel analysis)
- Fan-out jobs where Hermes would need to manually spawn >5 sub-agents
- Long-context, multi-step coordination tasks that benefit from Kimi K2.6's 200K context window
- Any job tagged: `fan-out`, `kimi`, `swarm-coordinator`, `parallel`, `batch`

## When NOT to use
- Simple single-model tasks → hermes_self
- Coding tasks → codex_cli / aider
- Browser automation → agent_zero / browser_use
- Small deliverables → openswarm
- Outbound phone/email → retell_channel

## How it works
1. Admiral routes job to `kimi_coordinator` runtime via A2A delegation
2. `src/agent_os/runtimes/kimi_coordinator/invoke.py` sends the job to the Kimi K2.6 Swarm Coordinator A2A endpoint
3. Kimi decomposes the task internally into up to 300 parallel sub-agent calls
4. Progress is published to NATS: `agents.kimi-coordinator.task.{task_id}`
5. The entire fan-out is wrapped in a Temporal `FanOutWorkflow` — kill Admiral mid-run, restart, Temporal resumes

## Cost & latency
- Kimi K2.6 pricing: $0.60/M input tokens, $3.00/M output tokens (75-83% savings via prompt caching)
- Tool-invocation success rate: 96.6%
- Latency: 5-60 minutes depending on fan-out depth
- Temporal workflow overhead: negligible

## Examples
- "Research the top 200 AI startups and produce a competitive landscape report"
- "Fan out this list of 50 companies to 50 parallel research agents"
- "Analyze all 300 customer support tickets from last month and categorize them"
- "Generate personalized outreach for 100 prospects in parallel"

## Configuration
- `KIMI_COORDINATOR_URL` — A2A endpoint for the deployed Kimi Swarm Coordinator
- `MOONSHOT_API_KEY` — Moonshot API key for Kimi K2.6
- `TEMPORAL_HOST` — Temporal server endpoint (default: localhost:7233)

## Alternatives (ordered)
1. **openswarm** — for smaller multi-deliverable jobs (<10 parallel agents)
2. **hermes_self** — for tasks that don't need true fan-out
3. **claude_managed** — for long-running single-model cloud tasks

## See also
- src/agent_os/runtimes/kimi_coordinator/invoke.py
- src/agent_os/workflows/fan_out.py
- deploy/temporal/railway.json
