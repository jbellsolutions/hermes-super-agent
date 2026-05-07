---
name: openswarm
runtime: openswarm
tier: 2
category: deliverable_production
cost_class: medium
risk_class: low
preferred_models: [claude-opus-4.7, gpt-5.5]
mcp_or_native: native
description: Use when the user asks for multi-deliverable production (slides, decks, research with charts, executive summaries, one-pagers), or wants to build a specialized agent swarm for a business purpose. Forks vendor/openswarm into per-purpose fleet members each with their own port/folder/.env.
---

## When to use
- Investor pitches, sales decks, research reports, executive summaries
- Multi-piece deliverables (deck + research + analysis + writeup in one ask)
- Building specialized swarms via op=build (the "agent-builder agent" — `/build-swarm`)
- Tasks where slide design + research depth + chart aesthetics + copy tone all need to be sharp

## When NOT to use
- Quick coding tasks → claude_subagents / codex_cli / aider
- Browser automation → browser_use
- Long shell grind → openclaw
- Pure research without deliverables → exa
- Single-doc writing → hermes_self

## Alternatives (ordered)
1. **hermes_self** — for simpler asks (single doc, no charts, no orchestration needed)
2. **openclaw** — when grind/file/shell dominates over deliverable polish
3. **claude_managed** — for >1hr cloud-resident pipelines

## Cost & latency
- Typical: $0.10–$2.00 per run (varies with depth, model)
- Latency: 5–30 minutes
- Per-swarm budget guard: warn at 80%, hard-block at 100%

## Examples
- "Create a complete investor pitch for X"
- "Research the AI agent framework market and turn it into a 10-slide deck with charts"
- "Build me an SEO swarm that does keyword research, competitor analysis, and writes blog posts"
- "Generate 5 pitch variants in parallel — technical, business, consumer, enterprise, regulatory"

## See also
- vault/decisions/openswarm-runtime-adoption.md
- src/agent_os/runtimes/openswarm/manifest.yaml
- README.md "OpenSwarm fleet" section
