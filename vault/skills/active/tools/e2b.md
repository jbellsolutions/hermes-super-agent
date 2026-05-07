---
name: e2b
runtime: e2b
tier: 2
category: sandbox_execution
cost_class: low
risk_class: low
preferred_models: [claude-sonnet-4.7, gpt-5.5]
mcp_or_native: native
description: E2B — clean VM per run for sandboxed code execution. Use when you want to run code that you can't or won't trust on your local machine, or need fresh environments for repro builds.
---

## When to use
- Running untrusted/agent-generated code safely
- Reproducible builds where state from prior runs would interfere
- Quick "does this snippet work" tests in a clean env
- Customer-facing "run their code, return result" demos

## When NOT to use
- Trusted code on your local machine → terminal / codex_cli
- Long-running cloud → claude_managed
- Browser tasks → browser_use / agent_zero
- Tasks that need persistent state → openclaw / agent_zero

## Alternatives (ordered)
1. **terminal** — when the code is trusted and local
2. **claude_managed** — for long-running cloud
3. **agent_zero** — when you also want a visual workspace

## Cost & latency
- Typical: $0.01–$0.50 per run
- Latency: 5–60s sandbox spin-up + actual execution

## Examples
- "Run this Python snippet a user pasted into Slack and return the output"
- "Build this Dockerfile in a clean env and check the image works"
- "Execute the candidate solution against the test harness, sandbox-isolated"

## See also
- src/agent_os/runtimes/e2b/manifest.yaml
- ECOSYSTEM-PLAYBOOK.md (layer 9)
