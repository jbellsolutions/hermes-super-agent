---
name: codex_cli
runtime: codex_cli
tier: 2
category: coding_background
cost_class: medium
risk_class: medium
preferred_models: [gpt-5.5]
mcp_or_native: native
description: Use for background coding via OpenAI Codex CLI — the default for GPT-5.5 coding work, multi-provider hedge against Anthropic outages. Best when you want to fire off coding tasks and continue with other work.
---

## When to use
- Background repo edits where you don't need to watch every step
- GPT-5.5-specific coding tasks (debug, security, auth, weak-test repos)
- Multi-provider hedge so a single Anthropic outage doesn't stop the press
- Authenticated locally; uses your existing Codex setup at /Users/home/.local/bin/codex

## When NOT to use
- Tight interactive loops → claude_subagents
- Git-aware single-file edits → aider
- Cloud-resident jobs → claude_managed
- Untrusted code → e2b

## Alternatives (ordered)
1. **claude_subagents** — when you want frontier Anthropic models in the coding loop
2. **aider** — for git-aware incremental edits
3. **deepseek-v4-pro** (model) — when Codex shells out and you want cheap frontier-class

## Cost & latency
- Typical: $0.10–$2.00 per task
- Latency: real-time per turn, fully autonomous on long tasks

## Examples
- "Fix the failing security test in auth/middleware.py"
- "Implement the OAuth2 device flow per RFC 8628 with tests"
- "Debug why this lambda times out under load"

## See also
- src/agent_os/runtimes/codex_cli/manifest.yaml
- docs/routing-intelligence-contract.md (Codex section)
