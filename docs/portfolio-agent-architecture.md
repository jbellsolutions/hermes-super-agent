# Portfolio Agent Architecture

This document answers the core operating question: should one Hermes instance run every business, or should each project/business have its own agent?

## Recommendation

Use a hub-and-spoke model.

```text
Justin / Operator
        │
        ▼
Primary Hermes Super Agent
(always-on command center, Telegram/Slack, portfolio memory)
        │
        ├── Project registry / manifest / dashboard
        ├── Shared tool library and setup standards
        ├── Shared vendor/runtime updates
        ├── Cross-project reporting and approvals
        │
        ├── Specialist Agent: COO / Ops Company
        ├── Specialist Agent: Agency Company
        ├── Specialist Agent: SDR / Paperclip Business
        ├── Specialist Agent: Content Engine
        └── Specialist Agent: Customer/Client Workspace
```

The primary Hermes agent remains the go-to operator. It should not ingest every detail of every business into one giant mixed context. It should hold the portfolio map, governance, reporting, and routing. Each serious business gets a specialist workspace/agent with its own memory, skills, vault, deploy target, and secrets.

## Why not one giant agent?

One giant agent eventually breaks because:

- Context from unrelated businesses bleeds together.
- Skills become too broad and conflict.
- Secrets and permissions become hard to isolate.
- Notion/Obsidian/Railway/DigitalOcean state becomes noisy.
- A mistake in one project can affect another.
- Commercial/customer deployments require isolation anyway.

## Why not completely separate agents with no hub?

A pile of isolated agents also breaks because:

- Justin becomes the human router.
- You lose portfolio-level reporting.
- Updates and skills drift across projects.
- Nobody owns cross-project cost, uptime, and deployment health.
- It becomes hard to sell because every install is bespoke.

## The operating model

### Primary Hermes Super Agent

Responsibilities:

- Own the portfolio/project registry.
- Know which specialist agent owns which business.
- Monitor Railway, DigitalOcean, GitHub, domains, and dashboards.
- Maintain setup docs and runbooks.
- Apply safe daily updates to shared framework pieces.
- Create/retire specialist agents.
- Route work to the right project agent.
- Summarize status back to Justin.

Should remember:

- Stable facts about the operator and portfolio.
- Which projects exist.
- Where each project lives.
- Who owns each workflow.
- How to reach each specialist agent/service.

Should not remember:

- Every campaign detail.
- Every customer conversation.
- Every project-specific prompt/skill.
- Every Notion/Obsidian page body.

### Specialist project/business agents

Responsibilities:

- Own one business, client, or vertical.
- Keep project-specific memory and skills.
- Run project-specific dashboard/workers.
- Use project-specific Railway/DigitalOcean resources.
- Maintain project-specific secrets and integrations.
- Report status back to the primary Hermes agent.

Examples:

- COO Agent — operations dashboard, uptime, daily briefing, deployment monitoring.
- Agent Company — multi-agent SDR/content/social teams.
- Paperclip Business — Paperclip dashboard for a specific zero-human-company offer.
- Client Workspace — isolated commercial deployment for one customer.

## Shared state vs isolated state

### Shared globally

- Super Agent repo and setup docs.
- Base skills/runbooks/templates.
- Tool install policies.
- Health check patterns.
- Commercial tier definitions.
- Portfolio dashboard summaries.

### Isolated per project/business/customer

- Secrets.
- Vault/memory.
- Conversation logs.
- Railway/DigitalOcean resources.
- Notion/Obsidian namespaces.
- Agent profiles and prompts.
- Customer data.
- Budget and approval rules.

## Deployment guidance

### Local-only experiments

Use a specialist Hermes profile or worktree first. Promote only if useful.

### Persistent internal business

Use Railway/DigitalOcean/VPS for the always-on worker/dashboard. Keep the primary Hermes agent as the control plane.

### Commercial/customer deployment

Use a separate deployment per customer/workspace. Do not share vaults or secrets. Optional Orgo AI cloud computer only for Enterprise tier where the customer pays for isolation/visible desktop.

## Paperclip relationship

Paperclip is best treated as the company dashboard/control plane for autonomous businesses, not as a replacement for Hermes.

- Hermes = conversational orchestrator and tool-using operator.
- Paperclip = org chart, goals, budgets, tickets, agent workforce visibility.
- Codex/Claude/OpenClaw/browser-use = workers/runtimes.
- Railway/DigitalOcean = persistence and execution surface.

For paperclip businesses, the primary Hermes agent should know the Paperclip company exists and monitor it. The Paperclip company should own its own execution state and worker agents.

## COO Agent and Agent Company relationship

- `coo-agent` becomes the operations/business-control-room template.
- `agent-company` becomes the agent-team hierarchy template.
- Super Agent becomes the framework that can spawn, manage, and update both patterns without creating another disconnected wrapper repo.

## First commercializable path

1. Build Super Agent as the primary command center.
2. Add a project registry with entries for COO Agent, Agent Company, and each Paperclip business.
3. Connect Railway and DigitalOcean read-only first to discover what is actually running.
4. Create one specialist project agent for one business.
5. Give it its own memory/vault/secrets/deploy target.
6. Have it report daily to the primary Hermes agent.
7. Productize that pattern as "spin up an agent-run business workspace."

## Anti-bloat rules

- A project gets its own specialist agent when it has its own customers, secrets, deploy target, or recurring workflows.
- Keep small one-off tasks inside the primary Hermes agent.
- Do not share project-specific memories across businesses.
- Do not duplicate core setup docs; update the Super Agent repo and let specialists inherit.
- Use manifests/project registry entries for orchestration instead of mental memory.

## Access needed next

To audit current paperclip businesses and dashboards, the primary Hermes agent needs read-only discovery first:

- Railway account/project access.
- DigitalOcean account/droplet/app access.
- GitHub repo access, already mostly available through `jbellsolutions` repos.
- SSH key discovery on the local machine.
- Deployment env summaries with secret values redacted.

After discovery, write:

- `vault/projects/<project>.md` per project.
- `docs/deployments-inventory.md` for what is actually running.
- `docs/portfolio-roadmap.md` for which specialist agents to spawn first.
