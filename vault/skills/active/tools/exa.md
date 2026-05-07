---
name: exa
runtime: exa
tier: 1
category: search
cost_class: low
risk_class: low
preferred_models: [claude-sonnet-4.7, gpt-5.5]
mcp_or_native: native
description: Exa neural search — programmatic "find me 10 articles about X" without spinning up a browser. Use for fast, structured search-to-artifact tasks.
---

## When to use
- "Find me N articles/papers/posts about X"
- Quick lookups that don't need full browser interaction
- Research feeds where the output is a list of URLs + summaries
- Background "what's been said about X recently" sweeps

## When NOT to use
- Pages requiring login or interaction → browser_use
- Specific page content extraction (single URL) → curl + parser
- Multi-source research with synthesis → openswarm (deep research)

## Alternatives (ordered)
1. **browser_use** — when you need to interact with the page after finding it
2. **openswarm/deep_research** — for multi-source synthesis
3. **hermes_self** — for known-answer questions (don't search)

## Cost & latency
- Typical: $0.01–$0.10 per query
- Latency: 1–5s per query

## Examples
- "Find 10 recent articles about AI agent frameworks"
- "What are the top 5 OSS multi-agent projects right now?"
- "Surface the last 3 incidents where a multi-agent system failed in production"

## See also
- src/agent_os/runtimes/exa/manifest.yaml
- ECOSYSTEM-PLAYBOOK.md (layer 10)
