# Builder Tool Architecture

_Last updated: 2026-05-02_

## Problem

The Super Agent should not become a random pile of tools, skills, and agent runtimes.

OpenClaw, Codex, Claude Code, Cursor SDK, Composio, MCP tools, Browser Use, and Symphony-style harnessing should fit into a coherent system where each component has a role.

## Principle

Separate:

1. **Brain / orchestrator** — decides what should happen.
2. **Control plane** — tracks state, companies, tasks, approvals, budgets, and health.
3. **Execution backends** — do specific kinds of work.
4. **Tool/data connectors** — connect to external systems.
5. **Harness / proof layer** — makes work safe, testable, and reviewable.

## Super Agent tool layers

```text
Primary Hermes Super Agent
  ├── Brain / Orchestrator
  │     Hermes main model, memory, skills, portfolio registry
  │
  ├── Business Control Plane
  │     COO specialist, Paperclip companies, scorecards, approvals
  │
  ├── Builder Swarm Harness
  │     WORKFLOW.md, isolated workspaces, task schema, proof-of-work
  │
  ├── Coding Backends
  │     Cursor SDK, Codex, Claude Code, OpenClaw, OpenCode, Hermes subagents
  │
  ├── Tool Connectors
  │     Composio, MCP servers, Google Workspace, Slack, Notion, GitHub, Railway, DigitalOcean
  │
  └── Computer/Browser Backends
        Browser Use, Agent Zero/A0, optional Orgo/cloud computer, Cursor cloud VMs
```

## Tool roles

### Hermes

Role: primary orchestrator and product shell.

Owns:

- user conversation
- memory/skills
- portfolio registry
- routing decisions
- approval gates
- repo/docs updates
- health/cost reports

### Paperclip

Role: optional visual business control plane.

Owns if promoted:

- companies/offers
- org charts
- budgets
- agent roster
- heartbeats
- dashboard visibility

Does not replace the Super Agent registry until programmatic control is proven.

### COO Specialist

Role: business cofounder/operator.

Owns:

- priorities
- scorecards
- operating cadence
- decisions/recommendations
- company CEO/team accountability

Does not own low-level tool installation or infrastructure mutation.

### Symphony

Role: harness pattern for coding work.

Owns conceptually:

- work item → isolated workspace → coding agent → tests/proof → PR/review
- task decomposition
- proof-of-work requirements
- review handoffs between frontier models and cheaper workers

Not a default runtime yet. Prefer the simplest effective harness: Cursor SDK + repo `WORKFLOW.md` may be enough. Adopt Symphony as an implementation/reference only if it adds measurable orchestration value beyond the simpler setup.

### Cursor SDK

Role: optional builder backend.

Best for:

- cloud coding agents
- Cursor-indexed repos
- TypeScript/JS-heavy work
- commercial “developer swarm” demos
- PR-generating tasks with visibility in Cursor

### Codex

Role: default strong coding backend where already authenticated.

Best for:

- GPT-5.5 coding tasks
- local worktrees
- repo edits with tests
- direct CLI-driven implementation

### Claude Code

Role: alternate coding backend and customer-compatible developer tool.

Best for:

- Claude-native repos
- users already operating in Claude Code
- long-form refactors where Claude Code conventions exist

### OpenClaw

Role: optional coding/runtime backend or migration source.

Use when already wired and useful. Do not force all new architecture through OpenClaw.

### Composio / MCP

Role: external tool connectors.

Best for:

- business systems
- SaaS APIs
- CRM/calendar/email/task management
- structured actions cheaper than browser/computer use

### Browser Use / Agent Zero / Orgo

Role: computer/browser fallbacks.

Use when:

- no API/MCP exists
- visual inspection is required
- customer/demo needs visible computer use
- isolated cloud desktop is worth the cost

## Runtime router

Use a policy router instead of hardcoding one winner:

```yaml
routing_policy:
  default_coding_backend: codex
  commercial_cloud_backend: cursor_sdk
  cheap_model_backend: deepseek
  frontier_architecture_review:
    - gpt-5.5
    - claude-opus-4.6-or-4.7
  high_risk_debug_security_auth_tests:
    - gpt-5.5
    - claude-opus-4.6-or-4.7
  content_design_brand_voice: claude-opus-4.6-or-4.7
  visual_fallback: browser_use_or_agent_zero
  enterprise_cloud_computer: orgo_optional
```

## Cost/intelligence policy

- Use DeepSeek/cheap models for mechanical, test-protected tasks.
- Use GPT-5.5 and Claude Opus 4.6/4.7 together for architecture, hard debugging, security, infra, auth, unit tests, weak-test repos, and high-risk deployment coding.
- Use Claude Opus 4.6/4.7 especially for content, design, brand voice, nuanced creative/business writing, and architecture review.
- Use Cursor SDK for its harness/runtime. Do not default to Cursor Composer unless it proves best for a specific task.
- Use Symphony as a guide for harness design if useful; do not add it as a required dependency if Cursor SDK + `WORKFLOW.md` is simpler and sufficient.
- Let harness proof, not model vibes, determine promotion.

## Tool access policy

Not every agent gets every tool.

- Primary Hermes can route to most tools/backends because it is the technical control plane.
- Specialist agents get scoped bundles matched to their role.
- Builder workers get repo/test/PR tools, not broad business or customer-data access.
- The Single Brain COO gets business tools and dashboards, not destructive infrastructure powers by default.
- Deployment health specialists get read-only infra tools unless explicitly elevated.
- Browser/computer backends are invoked only when the task requires them.

See `docs/routing-intelligence-contract.md` for the detailed routing and tool-bundle policy.

## Commercial packaging

### Operator

- Hermes
- Codex or Claude Code
- core MCP/API tools
- deployment health report
- portfolio registry

### Pro Operator

- Operator
- Paperclip dashboard
- Agent Zero/A0 or browser fallback
- builder swarm harness
- optional Cursor SDK backend

### Enterprise

- Pro Operator
- customer/project isolated workspaces
- Railway/DigitalOcean/VPS deployment
- optional Orgo/cloud computer
- Cursor cloud/self-hosted workers
- cost caps and audit logs

## First build order

1. Keep `WORKFLOW.md` as the universal coding-agent contract.
2. Add Cursor SDK as optional backend documentation.
3. Do a Cursor SDK POC only after `CURSOR_API_KEY` and cost cap are set.
4. Keep Codex as the default immediate coding backend because it is already installed/authenticated locally.
5. Use model/cost routing rather than choosing one model forever.
