# COO Single Brain Rebuild Plan

_Last updated: 2026-05-02_

## Decision

Rebuild the COO as the **Single Brain COO** using the Super Agent architecture and lessons from the existing `coo-agent`, `coo-platform`, `single-brain`, and `agentstack-hermes` assets.

Do not try to salvage the old `coo-platform` as-is unless source inspection proves it is the fastest safe base. It appears alive but not trusted. It can be shut down later after the replacement is live and verified.

## Mission

The COO is the other half of Justin:

- Justin is strongest in sales, marketing, relationships, product vision, and building energy.
- The COO must own operations, organization, decision cadence, accountability, scorecards, execution discipline, and business cofounder thinking.
- The COO should act like a YC-style operational cofounder: direct, practical, metric-driven, and willing to make organizational recommendations.

## Hierarchy

```text
Justin
  ├── Primary Hermes Super Agent
  │     Mission: everything builder, technical operator, repo/tool/deployment orchestrator
  │
  └── Single Brain COO
        Mission: business cofounder / COO / operator
        Reports to Justin; can ask Primary Hermes for technical changes
        └── Paperclip companies / offer teams
              One company per offer/business model
              Each has a CEO/lead agent, budget, goals, and approval gates
```

Primary Hermes remains above the COO technically. The COO can direct business work and request technical changes, but Hermes owns the stack, infrastructure, repo updates, and tool integration.

## Inputs to reuse

### `jbellsolutions/coo-agent`

Keep:

- COO identity and operational posture.
- MCP-first principle.
- Heartbeat concepts.
- Business playbooks.
- Verification/honesty rules.
- Daily/weekly/monthly reporting cadence.

Change:

- Stop assuming the Mac Mini + Claude Code + ClaudeClaw stack is the only architecture.
- Make Hermes the parent orchestrator/control plane.
- Make Paperclip optional/pluggable dashboard, not the only source of truth.
- Replace one-off SDR-specific defaults with generic offer/company/team primitives.

### Railway `coo-platform`

Keep only if useful:

- It has a live health check.
- It appears to be a console app with a monorepo layout.

But:

- Source repo is not mapped yet.
- Slack/chat behavior is not trusted.
- Treat it as legacy until proven otherwise.

### DigitalOcean `single-brain`

Use as:

- Concept name and intended identity.
- Possible existing memory/runtime source after SSH access is restored.

But:

- SSH currently blocked by missing accepted key.
- Public common HTTP ports time out.
- Do not mutate until mapped.

### Railway `agentstack-hermes`

Use as:

- Active Paperclip/Hermes runtime candidate.
- Paperclip UI/control surface.
- Existing Hermes API/scheduler/worker pattern.

Current state:

- Paperclip UI is live.
- Hermes API is live.
- Scheduler/worker heartbeat mock runs are live.
- `allowLiveRuns` is currently `false`, which is a good safety posture.

## Product shape

The COO should be a clean separate chat + dashboard-backed operating system.

Minimum v1:

- Separate Hermes profile/session/persona for COO.
- Dedicated COO memory/vault namespace.
- Business operating cadence:
  - morning priorities
  - daily report
  - weekly review
  - monthly strategy
- Portfolio registry access.
- Deployment health report access.
- Paperclip read adapter.
- Business decision log.
- Approval gates for money, outbound, hiring, production infra, customer communication, and legal/contract changes.

## First data model

```yaml
company:
  id: string
  name: string
  offer: string
  stage: idea|build|launch|sell|fulfill|scale|pause
  owner_agent: string
  weekly_goal: string
  north_star_metric: string
  budget_policy: string
  approval_policy: string
  dashboard_url: string
  repo_urls: []
  deployment_refs: []

coo_decision:
  id: string
  date: YYYY-MM-DD
  company_id: string
  decision: string
  rationale: string
  expected_impact: string
  approval_required: boolean
  status: proposed|approved|executing|done|rejected

heartbeat:
  date: YYYY-MM-DD
  company_id: string
  status: green|yellow|red|unknown
  wins: []
  blockers: []
  metrics: {}
  next_actions: []
```

## Rebuild path

### Phase 0 — Inventory and safety

- Keep `coo-platform` running until a replacement is proven.
- Do not shut down `single-brain` or `coo-platform` without a rollback plan.
- Map `agentstack-hermes` and Paperclip companies first.
- Restore SSH access to `single-brain` if possible.

### Phase 1 — Source-of-truth repo

Use `jbellsolutions/coo-agent` as the likely repo to refresh unless Justin chooses a new repo name.

Rebuild it as:

```text
coo-agent/
  README.md
  COO.md                       # identity, authority, boundaries
  WORKFLOW.md                  # coding-agent harness contract
  ops/
    COMMAND_CENTER.md
    AGENT_TEAM.md
    DAILY_OPERATING_SYSTEM.md
    EXECUTION_BACKLOG.md
    DECISION_LOG.md
    SCORECARD.md
  schemas/
    company.yaml
    coo_decision.yaml
    heartbeat.yaml
  runbooks/
    paperclip-adapter.md
    portfolio-registry.md
    slack-telegram-access.md
    approval-gates.md
```

### Phase 2 — COO runtime

Start with observe/report only:

- Daily business report.
- Weekly operating review.
- Pull deployment health report from primary Hermes.
- Read Paperclip state if authenticated.
- Create proposed decisions, not autonomous execution.

### Phase 3 — Paperclip company model

Each offer becomes a Paperclip company:

```text
Offer / Company
  ├── CEO agent
  ├── Operator/PM agent
  ├── Builder swarm access
  ├── Scorecard
  ├── Budget
  ├── Approval gates
  └── Weekly goals
```

The COO oversees all companies. Primary Hermes can modify the COO or any business team when Justin asks.

### Phase 4 — Controlled autonomy

Only after reporting is reliable:

- COO can assign tasks to company CEOs.
- COO can rebuke/nudge stalled teams.
- COO can request builder swarm tasks.
- COO can recommend pausing/killing offers.
- COO can execute approved recurring actions.

## Open questions for Justin

These do not block documentation, but they should be answered before live rebuild/deploy:

1. Should the refreshed source repo stay `jbellsolutions/coo-agent`, or should we create a new repo like `single-brain-coo`?
2. Should the first COO chat run as a separate Hermes profile, a separate Telegram bot/chat, or both?
3. What are the first 3 offers/companies the COO should manage in Paperclip?
4. Which business tools are mandatory on day one: Slack, Gmail, Calendar, GoHighLevel, Notion, ClickUp, Airtable, Google Sheets?
5. Should the legacy Railway `coo-platform` be archived only after the new COO passes a 7-day smoke test?
