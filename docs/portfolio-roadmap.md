# Portfolio Roadmap

_Last updated: 2026-05-02_

## Current answer

Use Hermes as the main everything-builder/hub, then create a separate business-only COO specialist after the reporting/control contracts are proven.

Justin's instinct is right:

- Primary Hermes Super Agent = everything hub, builder, infrastructure operator, repo updater, tool integrator, project router.
- COO Specialist = business-only CEO/COO persona focused on priorities, numbers, operations, offers, dashboards, and management cadence.
- Paperclip = possible dashboard/control plane for autonomous companies, but should be evaluated as a control plane, not blindly adopted as the whole brain.

## First infrastructure map

### Railway candidates

- `agentstack-hermes`
  - Services: `paperclip-server`, `hermes-worker`, `hermes-api`, `hermes-scheduler`, Postgres.
  - Why it matters: strongest candidate for existing Paperclip/Hermes always-on stack.

- `coo-platform`
  - Services: `console`, Postgres.
  - Why it matters: likely connected to the COO dashboard concept.

- `notion-pm-managed-agent-fleet`
  - Many Postgres services plus web.
  - Why it matters: may contain old agent-management/dashboard experiments.

- `ai-guy-flywheel`
  - Redis, browser-runner, worker, dashboard.
  - Why it matters: already shaped like a worker/dashboard agent system.

### DigitalOcean candidates

- `paperclip-ops`
  - Tags: `paperclip`, `operations`.
  - Why it matters: strongest DO candidate for Paperclip operations/control plane.

- `single-brain`
  - Tags: `single-brain`.
  - Why it matters: likely central-agent/single-brain experiment.

- `cold-email-agent`
  - Why it matters: persistent outbound worker; high approval sensitivity.

- `LinkedinLeadGen` / `kevin-leads`
  - Why it matters: lead-gen worker/customer-specific boxes.

## Specialist-agent sequence

### Phase 1 — Observe/report only

Build no new autonomy yet. The primary Hermes should answer:

- What is running?
- Is it healthy?
- Where is it deployed?
- What repo/business owns it?
- What does it cost?
- What broke recently?
- Does it need human approval?

Targets:

1. `paperclip-ops` droplet.
2. `agentstack-hermes` Railway project.
3. `coo-platform` Railway project.
4. `single-brain` droplet.

### Phase 2 — Business-only COO specialist

Create a separate COO Specialist after Phase 1 reporting works.

Mission:

- Business priorities.
- Daily/weekly operating cadence.
- Offer/project scorecards.
- Decision memos.
- Customer/business context.
- Does not own low-level infrastructure unless assigned.

Reports to:

- Primary Hermes Super Agent.

Primary Hermes keeps:

- Tool installation.
- Repo updates.
- Infrastructure discovery.
- Agent spawning.
- Cross-project routing.
- Technical execution.

### Phase 3 — Paperclip pilot

Pilot Paperclip for one company/workspace, not everything.

Best first use:

- One Paperclip company for a single business offer or internal operations workspace.
- Agents report heartbeats/status to Paperclip.
- Primary Hermes reads Paperclip status and reports to Justin.
- Primary Hermes can create tasks/issues in Paperclip only after a clear API/control path is proven.

Do not depend on Paperclip issue mechanics if they feel clunky. Use Paperclip initially for:

- Org chart.
- Company/workspace separation.
- Budgets.
- Heartbeats.
- Dashboard visibility.
- Agent roster.

Keep actual task/control routing abstracted so we can swap Paperclip later if needed.

## Paperclip evaluation

### What Paperclip looks good for

- Multi-company dashboard.
- Agent org charts.
- Cost/budget visibility.
- Heartbeats.
- Governance and audit trail.
- One visual place to click into companies.

### What to be cautious about

- Issue/task UX may not fit Justin's preferred workflow.
- If task creation feels slow or unnatural, do not force it.
- It may be better as visibility/governance than as the canonical task engine.
- Need to verify API/programmatic control before relying on it commercially.

### Recommended approach

Use Paperclip as a pluggable control-plane candidate:

```text
Primary Hermes
  ├── Portfolio registry / local manifests
  ├── Railway/DigitalOcean discovery
  ├── Specialist agent heartbeats
  └── Optional Paperclip dashboard adapter
```

If Paperclip works well programmatically, promote it to default Pro/Enterprise dashboard. If not, keep the manifest/registry as source of truth and use another dashboard later.

## Symphony / harness engineering evaluation

Source: `https://github.com/openai/symphony`

Symphony is an OpenAI engineering-preview orchestration service for coding agents. It polls Linear, creates isolated per-issue workspaces, launches Codex app-server sessions, and expects in-repo `WORKFLOW.md` contracts.

### Why it matters

Symphony is directly useful for the engineering side of Super Agent:

- It formalizes the "work item → isolated agent run → proof of work → review/handoff" loop.
- It reinforces harness engineering: make repos easy for agents to test, verify, and land work safely.
- It gives us a pattern for specialist coding agents that should not share one dirty workspace.
- It fits the hub-and-spoke model: primary Hermes routes work; Symphony-like runners execute repo issues in isolated workspaces.

### Where it fits

Add Symphony as a candidate runtime/control pattern under:

- `src/agent_os/runtimes/symphony/` later, or
- `docs/symphony-intake.md` first, or
- a Super Agent wrapper that implements the SPEC in Python rather than adopting the Elixir preview.

### Recommendation

Do not add Symphony as a default dependency yet.

Do adopt the pattern:

- Every serious repo gets a `WORKFLOW.md` or equivalent agent-run contract.
- Work should run in isolated per-issue/per-task workspaces.
- Agents must return proof: tests, PR, logs, screenshots/video when useful.
- Primary Hermes should manage work, not babysit every coding turn.

Use Symphony when:

- Linear becomes the source of truth for engineering work.
- We need many concurrent Codex coding runs.
- Repos have good tests/CI/harnesses.

Do not use Symphony when:

- The project is business ops, dashboards, or infrastructure discovery rather than coding tasks.
- Linear is not the work tracker.
- The repo lacks tests/CI; fix harness first.

## Recommended next build order

1. Finish read-only SSH mapping for `paperclip-ops`, `single-brain`, and key lead-gen/cold-email droplets.
2. Write project registry entries for each major deployment.
3. Create a daily deployment health report that primary Hermes can send to Justin.
4. Create one COO Specialist identity/workspace, initially observe/report only.
5. Pilot Paperclip against one workspace.
6. Add Symphony/harness engineering for coding-heavy repos after the deployment map is stable.

## What not to do yet

- Do not make Paperclip the only source of truth until its programmatic control path is verified.
- Do not make COO Platform the main brain until it proves task execution and reporting.
- Do not let outbound agents send campaigns without explicit approval gates.
- Do not run all businesses inside one shared Hermes memory.
- Do not spin up disconnected specialist agents without a heartbeat/reporting contract.
