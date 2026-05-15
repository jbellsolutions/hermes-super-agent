# Routing Intelligence Contract

_Last updated: 2026-05-07_

> **Programmatic enforcement (Phase F):** This document is the authoritative policy. The runtime read-side now ships in [`vault/skills/active/tools/`](../vault/skills/active/tools/) (per-tool SKILL.md), [`vault/graph/tool-catalog.yaml`](../vault/graph/tool-catalog.yaml) (machine-readable), and the planner stack in [`src/agent_os/orchestrator/`](../src/agent_os/orchestrator/) (tier_classifier, tool_planner, model_planner, plan_card). Use `agent-os plan` / `agent-os tier` / `agent-os tool <name>` / `agent-os models` to verify routing without invoking. Decision record: [`vault/decisions/tool-awareness-and-model-routing.md`](../vault/decisions/tool-awareness-and-model-routing.md).

## Purpose

The Super Agent should not give every agent every tool all the time. It should route work intentionally based on task type, risk, cost, context, proof requirements, and available credentials.

Justin prefers fewer tools that work extremely well over many tools that are half-used.

## Core principle

Every agent/tool/backend invocation should answer:

1. What is the task?
2. What skill/runbook applies?
3. What is the cheapest safe model/backend that can do it?
4. What tools are actually needed?
5. What proof is required?
6. What approval gate applies?
7. Where should the result be logged? Obsidian, Notion, repo, Paperclip, or all of them?

## Model routing

### Dual-frontier review: GPT-5.5 + Claude Opus 4.6/4.7

For the highest-value or highest-risk work, GPT-5.5 and Claude Opus 4.6/4.7 should work together rather than compete as a single default.

Use the dual-frontier path for:

- architecture
- debugging
- security
- authentication/authorization
- unit tests and weak-test repos
- infra/deployment decisions
- high-stakes coding
- system design

Default pattern:

1. One frontier model drafts or diagnoses.
2. The other frontier model reviews, critiques, and proposes alternatives.
3. The orchestrator merges the answer into one implementation plan or patch.
4. Tests, proof, and approval gates decide whether to ship.

Claude may be equal or better for architecture in many cases; do not relegate Claude only to content/design. GPT-5.5 remains preferred for hard security/auth/debugging judgment, but the commercial Super Agent should use both where quality matters more than cost.

### Claude Opus 4.6/4.7

Especially strong for:

- content
- design
- brand voice
- landing pages and creative direction
- nuanced strategy writing
- high-quality synthesis
- architecture and system design review

### GPT-5.5

Especially strong for:

- hard debugging
- security
- authentication/authorization
- weak-test repos
- deployment logic
- high-stakes coding decisions

### Claude Sonnet 4.6 / 4.7

Default conversational + light orchestration model. Use for:

- normal Hermes turn handling and routing decisions
- short-to-medium responses where Opus is overkill
- subagent delegation where the parent reasoning sits in Opus
- everyday content that doesn't need brand-tier polish

Sonnet is the cheapest Anthropic tier ($3/$15 per Mtok) that still handles tool-use, vision, and chain-of-tool reasoning cleanly. Tier-1 banners default to Sonnet; Tier-2/3 plans escalate to Opus when the task class warrants it.

### DeepSeek v4 Pro

Use for:

- lower-cost legwork
- mechanical coding
- test-protected tasks
- repetitive refactors
- data extraction/cleanup
- worker/scheduler subtasks

DeepSeek v4 Pro ($0.27/$1.10 per Mtok) replaces the older v3 line as the cheap-coding default when Kimi K2's long-context strengths aren't needed. Both are eligible for builder-worker bundles.

### Kimi K2

Use for:

- cheap mechanical coding with very long context (100k+ tokens of source)
- bulk refactors across many files in one pass
- long-document analysis where Opus is too expensive to fan out
- background grind tasks that are test-protected

Kimi K2 ($0.15/$2.50 per Mtok via OpenRouter) sits alongside DeepSeek v4 Pro in the cheap-coding tier. Pick Kimi when the task is context-dominated; pick DeepSeek when it's logic-dominated.

### Gemini 2.5 Pro

Use for:

- multimodal research (images + PDFs + screenshots in one prompt)
- very-long-context document synthesis (1M-token window)
- cross-document grounding where the source set doesn't fit Opus
- pre-deck research passes that aggregate dozens of pages

Gemini 2.5 Pro ($1.25/$5 per Mtok) is the long-context multimodal complement to the dual-frontier pair — used in research + synthesis legs of OpenSwarm pipelines, not architecture/security judgment.

### Cursor Composer / Cursor models

Do not default to Cursor Composer just because Cursor SDK is present.

Cursor SDK is valuable primarily as a harness/runtime/backend. Use Cursor-supported models only when they prove best for the specific coding task or cost profile.

Justin's current preference is to avoid relying on Cursor Composer as a primary model; use the SDK for orchestration/harness value and route model selection separately.

## Backend routing

### Codex

Use for:

- local coding stack
- repo edits where Codex is already authenticated
- GPT-5.5 coding tasks
- worktree-based implementation

### Claude Code

Use for:

- Claude-native projects
- projects with existing Claude Code conventions
- content/design/code tasks that benefit from Opus/Sonnet behavior

### Cursor SDK

Use for:

- cloud coding-agent runs
- commercial builder-swarm demo
- PR-generating coding tasks
- spinning up coding teams under a structured harness
- repos where Cursor's indexing, cloud VM, hooks, skills, and UI visibility help

Cursor SDK can be the execution backend for coding teams while GPT-5.5 and Claude Opus 4.6/4.7 provide architecture/review judgment. Use Symphony as a harness pattern/reference when it helps with isolated workspaces, task decomposition, proof-of-work, test gates, and PR handoffs. Do not require Symphony as a runtime dependency unless it clearly beats a simpler Cursor SDK + repo `WORKFLOW.md` setup.

### Hermes subagents

Use for:

- quick parallel research/review/debug subtasks
- isolated analysis
- low-overhead worker tasks inside the current orchestration

### OpenClaw

Use when:

- a project already has useful OpenClaw wiring
- OpenClaw-specific behavior is needed
- migrating or inspecting old OpenClaw/ClaudeClaw-style systems

Do not force new architecture through OpenClaw by default.

## Browser/computer backend routing

### Browser Use

Use for:

- web automation where a browser library is enough
- scraping/QA flows
- lower-cost visual workflows than a full computer

### Agent Zero / A0

Use for:

- local visual computer workspace
- host-machine operations with Codex access
- debugging/inspection where visual UI and shell together help

### Orgo / managed cloud computer

Use only when:

- a customer/project needs isolated persistent cloud computer
- enterprise demo value justifies cost
- browser/computer use must survive local machine downtime

### Cursor Cloud VM

Use for:

- coding tasks, not general business GUI tasks
- Cursor SDK cloud runs
- isolated repo workspaces and PR generation

## Tool access bundles

Agents should receive role-specific bundles.

### Primary Hermes

- repo/file/terminal tools
- Railway/DigitalOcean inventory
- GitHub
- Obsidian/Notion sync
- delegation/cron
- controlled browser/computer tools

### Single Brain COO

- Obsidian/Notion
- Paperclip read/control adapter
- Slack/Gmail/Calendar/GHL/Sheets as approved
- deployment health report reads
- no direct destructive infra by default

### Per-business CEO specialist

- company scorecard
- company tasks/issues
- company budget
- approved business tools only
- no cross-company secrets

### Builder worker

- repo/worktree
- test/lint/build commands
- GitHub PR tools if approved
- no broad business tools unless task requires them

### Deployment health specialist

- read-only Railway/DigitalOcean
- read-only public health checks
- read-only SSH only when key/access approved
- Obsidian/Notion report writer
- no restart/redeploy/delete privileges

## Routing schema

```yaml
route_request:
  task_type: architecture|debugging|content|design|mechanical_coding|deployment_health|business_ops|browser_task
  risk: low|medium|high|critical
  preferred_model: auto|gpt-5.5|claude-opus-4.7|claude-sonnet-4.7|claude-sonnet-4.6|deepseek-v4-pro|kimi-k2|gemini-2.5-pro
  backend: auto|codex|claude_code|cursor_sdk|hermes_subagent|openclaw|browser_use|agent_zero|orgo
  tool_bundle: primary_hermes|coo|paperclip_company|builder|deployment_health
  proof_required: []
  approval_required: boolean
  log_targets:
    - obsidian
    - notion
    - repo
    - paperclip
```

The runtime model registry that backs `preferred_model: auto` lives at [`src/agent_os/orchestrator/config/models.yaml`](../src/agent_os/orchestrator/config/models.yaml) — edit pricing and task-class tags there, not in this document.

## Important answer: does everything have access to everything?

No. That would be dangerous, expensive, and confusing.

The intended design is:

- Primary Hermes can route to most tools/backends.
- Specialist agents get scoped tool bundles.
- Builder workers get coding tools, not broad business access.
- COO gets business tools, not destructive infra by default.
- Computer/browser tools are invoked when needed, not always available everywhere.
- Each route should be logged with the reason it chose that backend/model.
