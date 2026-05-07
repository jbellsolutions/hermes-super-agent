---
name: hermes_self
runtime: hermes_self
tier: 1
category: orchestrator
cost_class: low
risk_class: low
preferred_models: [claude-sonnet-4.6, claude-opus-4.7]
mcp_or_native: native
description: Default. Use when the task can be answered conversationally, with a single doc or short artifact, and no specialist runtime adds clear value. Hermes itself with sub-agents handles most work.
---

## When to use
- Conversational answers, quick research, one-shot writing
- Coordination tasks where Hermes routes to other tools but the heavy lift is decision-making
- Memory/skill recall, vault lookups, /explain queries
- Anything where spinning up a runtime would be overkill

## When NOT to use
- Multi-deliverable production (slides + research + docs) → openswarm
- Repo coding work → claude_subagents / codex_cli / aider
- Browser automation → browser_use
- Long shell/file grind → openclaw
- Cloud-resident jobs > 1hr → claude_managed

## Alternatives (ordered)
1. **openswarm** — when the task wants a deck, report, or multi-piece deliverable
2. **claude_subagents** — when the task is interactive coding in this repo
3. **exa** — when the task is "find 10 articles about X"

## Cost & latency
- Typical: $0.01–$0.30 per turn
- Latency: < 5s for short tasks, ~30s for synthesis

## Examples
- "What's the routing rule for the openclaw runtime?"
- "Summarize the last 3 incident postmortems"
- "Explain how the upgrader works"

## See also
- ARCHITECTURE.md (routing tree)
- src/agent_os/orchestrator/adapters/job_router.py
