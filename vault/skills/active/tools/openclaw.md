---
name: openclaw
runtime: openclaw
tier: 2
category: autonomous_grind
cost_class: medium
risk_class: medium
preferred_models: [gpt-5.5, claude-opus-4.7]
mcp_or_native: native
description: Use when the task is autonomous shell + file + browser grind that runs for many minutes. OpenClaw earned its slot via fastest-growing-OSS pressure-tested community velocity. Wraps vendor/openclaw.
---

## When to use
- Long-running shell pipelines (scrape → clean → enrich → dedupe 1000s of rows)
- File-system heavy tasks (find/replace across thousands of files, bulk renames)
- Browser-grind jobs where structured automation alone isn't enough
- Migration jobs from legacy ClaudeClaw/OpenClaw setups

## When NOT to use
- Interactive coding in a repo → claude_subagents / codex_cli / aider
- Multi-deliverable production (decks, reports) → openswarm
- Quick browser tasks (form fill, single page scrape) → browser_use
- Untrusted code execution → e2b
- Default tasks that need clear approval gates → hermes_self

## Alternatives (ordered)
1. **claude_managed** — for >1hr cloud-resident grind, no local machine dependency
2. **terminal** — for simple cron-style scripts (no autonomous loop)
3. **e2b** — when the work needs sandbox isolation

## Cost & latency
- Typical: $0.20–$5.00 per run depending on duration
- Latency: 5 min – 4 hours

## Examples
- "Scrape and dedupe 1000 leads from these sites, output CSV"
- "Find all references to deprecated API X across the codebase, generate migration plan"
- "Run this 200-step browser sequence and log every state transition"

## See also
- src/agent_os/runtimes/openclaw/manifest.yaml
- ECOSYSTEM-PLAYBOOK.md (layer 3)
