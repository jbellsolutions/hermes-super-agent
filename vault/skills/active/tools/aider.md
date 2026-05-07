---
name: aider
runtime: aider
tier: 2
category: coding_git_incremental
cost_class: low
risk_class: low
preferred_models: [claude-sonnet-4.7, deepseek-v4-pro]
mcp_or_native: native
description: Use for git-aware incremental coding where each change is a clean commit. Aider auto-commits per change, enabling easy rollback per turn. Best for surgical edits and refactors.
---

## When to use
- Surgical code changes that should be one commit per change
- Renames across files where git history matters
- Mechanical refactors with frequent commit gates
- Working in repos that benefit from Aider's auto-commit pattern

## When NOT to use
- Big architectural changes → claude_subagents
- Background firehose → codex_cli
- Repos that don't want a flood of small commits → claude_subagents
- Untrusted code → e2b

## Alternatives (ordered)
1. **claude_subagents** — for larger interactive sessions
2. **codex_cli** — for background firehose work
3. **terminal** — for one-shot scripts

## Cost & latency
- Typical: $0.05–$0.50 per turn (lower with deepseek-v4-pro / kimi-k2)
- Latency: real-time

## Examples
- "Rename `getUserId` to `getCurrentUserId` everywhere with one commit per file"
- "Add a docstring to every public function in this module"
- "Split this 800-line file into 4 smaller ones, one commit per split"

## See also
- src/agent_os/runtimes/aider/manifest.yaml
- vendor/aider (upstream)
