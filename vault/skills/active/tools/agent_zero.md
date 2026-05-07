---
name: agent_zero
runtime: agent_zero
tier: 2
category: visual_autonomous_workspace
cost_class: medium
risk_class: medium
preferred_models: [claude-opus-4.7, gpt-5.5]
mcp_or_native: native
description: Visual autonomous browser + host bridge. Use when the task benefits from a visible UI you can watch in real time AND needs host machine (Mac filesystem/commands) access. Dockerized at localhost:5080 with the A0 connector exposing host commands and Codex.
---

## When to use
- Visual debugging where seeing the browser interaction matters
- Tasks that mix browser work with host filesystem/commands
- Demos and customer-facing visible automation
- Cases where an autonomous loop benefits from human-watchable UI

## When NOT to use
- Pure browser automation without host access → browser_use (cheaper, simpler)
- Long unwatched grind → openclaw
- Coding tasks → claude_subagents / codex_cli
- Untrusted code → e2b (sandbox)

## Alternatives (ordered)
1. **browser_use** — when host access isn't needed
2. **computer_use** — for native desktop work outside the browser
3. **openclaw** — for headless long-running browser/shell grind

## Cost & latency
- Typical: $0.10–$1.00 per run (depends on model + duration)
- Latency: 1–60 minutes
- Local Docker overhead: minimal once warm

## Examples
- "Watch as you book a flight on this site, then summarize what blocked you"
- "Use the host machine to read this folder, then upload contents via the dashboard UI"
- "Demo to a customer: fill out their CRM workflow visibly"

## See also
- runbooks/agent-zero.md (install verified path)
- runbooks/a0-connector.md (host-bridge setup)
- src/agent_os/runtimes/agent_zero/manifest.yaml
