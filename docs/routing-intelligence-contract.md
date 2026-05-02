# Routing Intelligence Contract

_Last updated: 2026-05-02_

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

### GPT-5.5

Use for:

- architecture
- hard debugging
- security
- authentication/authorization
- weak-test repos
- infra/deployment decisions
- high-stakes coding
- system design

### Claude Opus 4.7

Use for:

- content
- design
- brand voice
- landing pages and creative direction
- nuanced strategy writing
- high-quality synthesis

### DeepSeek

Use for:

- lower-cost legwork
- mechanical coding
- test-protected tasks
- repetitive refactors
- data extraction/cleanup
- worker/scheduler subtasks

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
- repos where Cursor's indexing, cloud VM, hooks, skills, and UI visibility help

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

### Paperclip company CEO

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
  preferred_model: auto|gpt-5.5|opus-4.7|deepseek
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

## Important answer: does everything have access to everything?

No. That would be dangerous, expensive, and confusing.

The intended design is:

- Primary Hermes can route to most tools/backends.
- Specialist agents get scoped tool bundles.
- Builder workers get coding tools, not broad business access.
- COO gets business tools, not destructive infra by default.
- Computer/browser tools are invoked when needed, not always available everywhere.
- Each route should be logged with the reason it chose that backend/model.
