---
name: claude_subagents
runtime: claude_subagents
tier: 2
category: coding_interactive
cost_class: medium
risk_class: medium
preferred_models: [claude-opus-4.7, claude-sonnet-4.7]
mcp_or_native: native
description: Use for interactive coding inside this repo with Claude Code subagents — direct, in-repo, with tests/verification in the same loop. The default coding runtime when working at the keyboard.
---

## When to use
- Repo edits with tests, refactors, feature implementation
- Pair-programming style tasks where you'll review every change
- Anything in a Claude-native repo with existing skills/conventions
- Architecture work that benefits from Opus's synthesis

## When NOT to use
- Background coding while you're doing other things → codex_cli
- Git-aware incremental edits across a single file → aider
- Cloud-resident long-running coding → claude_managed
- Mechanical refactors that don't need frontier intelligence → deepseek-v4-pro / kimi-k2 (cheap models)
- Untrusted code execution → e2b

## Alternatives (ordered)
1. **codex_cli** — when you want OpenAI/GPT-5.5 in the coding loop
2. **aider** — for git-aware incremental work
3. **claude_managed** — for >1hr cloud jobs

## Cost & latency
- Typical: $0.20–$3.00 per session
- Latency: real-time (interactive)

## Examples
- "Add tests for the openswarm builder rollback flow"
- "Refactor the channel adapter to extract a common base class"
- "Implement the new tool catalog generator end-to-end"

## See also
- src/agent_os/runtimes/claude_subagents/manifest.yaml
- docs/routing-intelligence-contract.md (model section)
