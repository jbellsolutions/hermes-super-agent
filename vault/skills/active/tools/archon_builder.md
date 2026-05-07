---
name: archon_builder
runtime: a2a_delegate
tier: 2
category: agent_spawning
cost_class: low
risk_class: medium
preferred_models: [claude-opus-4.7, claude-sonnet-4.7]
mcp_or_native: native
description: Delegate "create a specialist agent" requests to Archon (coleam00/Archon) via A2A. Archon generates AGENT.md + skills + Railway deploy config from a natural-language spec, then Admiral deploys and registers the new agent.
---

## When to use
- "Create a LinkedIn outreach specialist"
- "Build me a [domain] specialist agent"
- Any job tagged: `build-specialist`, `archon`, `new-agent`

## When NOT to use
- Full superagent provisioning (own VPS + sub-fleet) → use `spawn-superagent` tag → `vps_spawn` runtime
- Building OpenSwarm deliverable swarms → `openswarm` runtime
- Coding tasks → codex_cli / aider

## How it works
1. Admiral routes `build-specialist` tagged job to `a2a_delegate` runtime
2. `invoke.py` delegates to Archon's A2A endpoint with natural-language spec
3. Archon generates:
   - AGENT.md (identity, mission, model, tools, approval rules)
   - Skill definitions
   - Railway deploy config
4. Admiral takes output, deploys to Railway via Railway API
5. New agent boots, registers its A2A endpoint with Admiral via NATS
6. Admiral subscribes to new agent's heartbeat
7. Agent is live and reporting within ~15 minutes

## Approval gate
- Tier 2 — plan card shown to user in Telegram with 3s grace + /cancel
- Plan card shows: agent name, skills, estimated cost/month, deployment target

## Cost & latency
- Archon generation: <$0.10 in LLM cost
- Railway deploy: ~10 minutes to live
- Railway container: ~$5/month per specialist

## Examples
- "Create a LinkedIn outreach specialist that sends connection requests and messages"
- "Build a Twitter monitoring agent that alerts me to mentions of our brand"
- "Spin up a competitive intelligence agent that watches 20 competitor websites"

## Configuration
- `ARCHON_A2A_URL` — Archon service A2A endpoint
- `RAILWAY_API_KEY` — Railway API key for automated deployment

## See also
- src/agent_os/orchestrator/spawner.py
- templates/AGENT.md.j2
- vault/skills/active/tools/coordinator.md
