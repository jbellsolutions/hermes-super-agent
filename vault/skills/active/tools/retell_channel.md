---
name: retell_channel
runtime: retell_channel
tier: 3
category: outbound_comms
cost_class: low
risk_class: high
preferred_models: [claude-sonnet-4.7, claude-opus-4.7]
mcp_or_native: native
description: Outbound phone calls via Retell AI (600ms latency, fastest in class). Same COO Specialist Hermes brain, different channel. Tier 3 by default — requires explicit YES in Telegram before any call is placed.
---

## When to use
- Outbound phone campaigns routed through COO Specialist Hermes
- Follow-up calls after cold email sequences
- Any job tagged: `phone`, `retell`, `outbound-phone`, `call`

## When NOT to use
- Cold email → use `email` tag instead (routes to Instantly.ai via same runtime)
- Inbound voice handling → livekit
- Browser or web tasks → agent_zero / browser_use

## How it works
1. COO Specialist Hermes receives a job with `phone` or `outbound-phone` tag
2. Tier classifier forces Tier 3 — hard stop, explicit YES required
3. Admiral emits plan card to Telegram: call list, script preview, estimated duration
4. On YES: `retell_channel/invoke.py` hits Retell AI API, places calls
5. Retell bridges to LLM (COO Specialist model) for real-time voice handling
6. Outcomes published to NATS: `agents.coo-specialist.task.completed`

## Approval gate (mandatory)
- Always Tier 3. No exceptions.
- Plan card shows: call list (first 5 recipients), script preview, estimated minutes, cost
- Override: `/tier 3 YES` in Telegram confirms and proceeds

## Cost & latency
- Retell AI: ~$0.05/min (fastest: 600ms response vs VAPI 700ms, Bland 800ms)
- LLM cost: billed against the COO Specialist model
- Latency to first ring: <2 seconds from job confirmation

## Examples
- "Call the 10 leads from yesterday's email campaign and follow up"
- "Place outbound calls to all prospects who opened our email but didn't reply"
- "Schedule a call campaign for the enterprise list"

## Configuration
- `RETELL_API_KEY` — Retell AI API key
- `RETELL_AGENT_ID` — pre-configured Retell agent ID (points to COO Specialist Hermes)

## See also
- src/agent_os/runtimes/retell_channel/invoke.py
- vault/skills/active/tools/archon_builder.md
- src/agent_os/orchestrator/config/identities/coo.yaml
