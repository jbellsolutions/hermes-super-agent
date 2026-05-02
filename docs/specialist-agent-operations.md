# Specialist Agent Operations

## Goal

Let Justin keep chatting with one primary agent while serious businesses/projects run as isolated specialist agents that can report up, be monitored, and eventually be controlled by the primary Hermes Super Agent.

## Short answer

Justin should not personally manage a dozen separate chats. The primary Hermes Super Agent should remain the command center. Specialist agents should be created by the primary agent using repeatable templates, registered in the project registry, and monitored through heartbeats/reports.

## Control levels

### Level 1 — Observe and report

Specialist agent runs separately. Primary Hermes can see:

- Health status.
- Last heartbeat.
- Current task queue.
- Recent outputs.
- Error logs.
- Cost/budget usage.
- Links to dashboards/deployments.

This is the minimum viable architecture and the safest first version.

### Level 2 — Rebuke / nudge / assign

Primary Hermes can send structured messages to the specialist:

- `pause`
- `resume`
- `nudge`
- `assign task`
- `request report`
- `escalate to Justin`

This keeps specialists separate but lets the command center steer them.

### Level 3 — Controlled execution

Primary Hermes can trigger approved workflows on specialist agents:

- Run daily report.
- Run deployment health check.
- Run backlog grooming.
- Open PR.
- Start a campaign after approval.

Risky actions still require approval gates.

### Level 4 — Full delegated autonomy

Specialist agents act continuously within budgets and policies. Primary Hermes monitors exceptions, reports status, and only intervenes when thresholds trigger.

This is the Enterprise/commercial goal, not the first step.

## How to spin up a specialist agent

The primary Hermes agent should be able to create these. Justin should not have to do it manually every time.

### Step 1 — Choose isolation boundary

Use a specialist agent when a project has any of:

- Its own customers.
- Its own secrets/API keys.
- Its own Railway/DigitalOcean deployment.
- Its own recurring workflows.
- Its own Notion/Obsidian namespace.
- Its own dashboard or Paperclip company.

### Step 2 — Create a workspace

Suggested local layout:

```text
~/agent-workspaces/
  coo-platform/
    vault/
    .env
    AGENT.md
    manifest.yaml
    reports/
    logs/
  agent-company/
  paperclip-sdr-business/
```

Suggested deployed layout:

```text
Railway/DigitalOcean project
  specialist-agent service
  dashboard service, optional
  database/queue service, optional
  heartbeat endpoint
  report artifact storage
```

### Step 3 — Give it an identity file

Each specialist gets an `AGENT.md`:

```markdown
# Agent Identity: COO Platform Specialist

Mission: Own the COO Platform deployment and daily operations dashboard.

Reports to: Primary Hermes Super Agent.

Owns:
- Railway project: coo-platform
- Repo: https://github.com/jbellsolutions/coo-agent
- Vault: ./vault
- Daily report: ./reports/daily.md

May do without approval:
- Read logs.
- Run tests.
- Summarize deployment status.
- Open non-destructive PRs.

Requires approval:
- Production deploys.
- Infrastructure deletion/scaling.
- Sending outbound messages.
- Changing billing/secrets.
```

### Step 4 — Register it with the primary Hermes

Create a registry entry in the Super Agent repo:

```yaml
id: coo-platform
name: COO Platform Specialist
status: active
owner: primary-hermes
repo: https://github.com/jbellsolutions/coo-agent
railway_project: coo-platform
vault: ~/agent-workspaces/coo-platform/vault
heartbeat_url: TBD
report_path: ~/agent-workspaces/coo-platform/reports/daily.md
control_level: observe-and-report
approval_required:
  - production deploys
  - destructive infra changes
  - outbound sending
```

### Step 5 — Add heartbeat/reporting

Minimum reporting contract:

```json
{
  "agent_id": "coo-platform",
  "status": "green|yellow|red",
  "last_seen": "ISO-8601 timestamp",
  "current_task": "short text",
  "blocked_on": [],
  "cost_today_usd": 0.0,
  "needs_human": false,
  "summary": "one paragraph"
}
```

This can be implemented as:

- File written to `reports/status.json`.
- HTTP endpoint `/status`.
- Paperclip heartbeat.
- Railway log scraper in the short term.
- Hermes cron job that asks each specialist for a report.

### Step 6 — Add control channel

Initial control channel can be simple:

- GitHub issue assignment.
- A queue table in Postgres.
- A file drop: `inbox/tasks/*.md`.
- Paperclip task.
- HTTP endpoint: `POST /tasks`.
- Telegram/Slack DM for human-facing specialists.

## Keeping one chat with Justin

Justin chats with primary Hermes only.

Primary Hermes says:

> "COO Platform is yellow: Railway service is up, but daily report failed because the database connection env var is missing. I can ask the COO specialist to open a fix PR, or I can inspect it myself."

Justin replies:

> "Have the COO specialist open the PR. Do not deploy."

Primary Hermes sends a structured task to the specialist, monitors it, and reports back.

## First specialist agents to create

Based on current repo/deployment discovery:

1. `coo-platform` / `coo-agent`
   - Role: operations-control-room template.
   - Why first: closest to the primary Hermes/COO concept.

2. `agentstack-hermes`
   - Role: existing always-on Hermes/Paperclip stack candidate.
   - Why: Railway project already has `paperclip-server`, `hermes-worker`, `hermes-api`, `hermes-scheduler`.

3. `agent-company`
   - Role: multi-agent hierarchy template.
   - Why: provides CEO/lead/worker pattern for business workforces.

4. One Paperclip business
   - Role: dashboard/control-plane for a single agent-run business.
   - Why: validates the sellable "agent company in a box" offer.

## Recommended first build

Start with Level 1 observe/report for `coo-platform` and `agentstack-hermes`.

Do not attempt full control immediately. First make the primary Hermes able to answer:

- What is running?
- Is it healthy?
- What repo owns it?
- What does it cost?
- What broke recently?
- Who/what should fix it?

Then add nudge/assign controls.

## Commercial version

For customers, specialist agents are sold as isolated workspaces:

- One primary operator agent.
- One or more specialist business agents.
- Dashboard/Paperclip view.
- Approval gates.
- Daily report.
- Optional managed cloud computer for Enterprise.

This is scalable because each customer/business has isolated state, while the framework and setup process stay shared.
