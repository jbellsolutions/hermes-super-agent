---
name: claude_managed
runtime: claude_managed
tier: 3
category: long_running_cloud
cost_class: high
risk_class: high
preferred_models: [claude-opus-4.7]
mcp_or_native: native
description: Anthropic Claude Managed Agents — long-running cloud-resident jobs (>1hr). Use when the task survives independently of your machine and you don't want to babysit. Tier 3 because it's expensive and runs without immediate oversight.
---

## When to use
- Multi-hour autonomous jobs that should survive your laptop closing
- Cloud-resident research or build pipelines (>1hr)
- Tasks where Anthropic's managed agent infrastructure adds value
- High-stakes runs that need their own logs, retries, isolation

## When NOT to use
- Anything < 1hr → openclaw / claude_subagents / codex_cli
- Untrusted code → e2b
- Customer demos → orgo (visible cloud computer)
- Quick iterative work → hermes_self

## Alternatives (ordered)
1. **openclaw** — for local long-running grind (cheaper, no cloud handoff)
2. **e2b** — for sandboxed bursts (not "managed", but isolated)
3. **claude_subagents** — when the task is < 1hr after all

## Cost & latency
- Typical: $1.00–$50.00 per run (varies wildly with duration)
- Latency: 1–24 hours
- **Tier 3 confirm required** before launch

## Examples
- "Run a 6-hour research pipeline on these 200 companies"
- "Process this 10GB log archive and produce a forensics report"
- "Generate documentation for every function in this 50K-line monorepo"

## See also
- src/agent_os/runtimes/claude_managed/manifest.yaml
- docs/routing-intelligence-contract.md (long-running cloud)
