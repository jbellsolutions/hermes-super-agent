---
name: terminal
runtime: terminal
tier: 1
category: scripts
cost_class: low
risk_class: low
preferred_models: [claude-sonnet-4.7, deepseek-v4-pro]
mcp_or_native: native
description: Plain cron-style scripts — one-shot terminal commands with no autonomous loop. Use when you know exactly what command to run and just need it run.
---

## When to use
- Running known cron-schedulable scripts
- One-shot terminal commands (`uv sync`, `git pull`, `pnpm install`)
- Tasks that fit cleanly into one shell invocation
- Build/deploy steps with no agent decision-making

## When NOT to use
- Anything autonomous → openclaw
- Sandboxed/untrusted → e2b
- Tasks that need decision-making between steps → claude_subagents
- Long-running with retry → claude_managed

## Alternatives (ordered)
1. **openclaw** — when the task needs an autonomous loop
2. **e2b** — when sandbox isolation is needed
3. **codex_cli** — when the script involves code generation

## Cost & latency
- Typical: $0 (no LLM call) to $0.02 (small wrapper)
- Latency: actual command runtime

## Examples
- "Run uv sync"
- "Execute the nightly upgrader (`uv run agent-os upgrade`)"
- "Pull latest from main and rebuild the manifest graph"

## See also
- src/agent_os/runtimes/terminal/manifest.yaml
- scripts/ folder for known commands
