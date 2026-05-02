# Project: agentstack-hermes

## Type

Railway project / active Paperclip + Hermes stack candidate.

## Deployment

- Provider: Railway
- Project: `agentstack-hermes`
- Project ID: `9981951a-4f01-4b8d-9ec9-36aa73f65041`
- Environment: `production`
- Environment ID: `2732dee8-55f0-4d4e-99ce-c49e6dc0a395`
- Services:
  - `paperclip-server` — latest deployment `SUCCESS`, Dockerfile builder
  - `hermes-api` — latest deployment `SUCCESS`, Railpack builder
  - `hermes-worker` — latest deployment `SUCCESS`, Dockerfile builder
  - `hermes-scheduler` — latest deployment `SUCCESS`, Railpack builder
  - `Postgres` — latest deployment `SUCCESS`
  - `Postgres-ek7H` — latest deployment `SUCCESS`

## Public endpoints observed

- Hermes API health: `https://hermes-api-production.up.railway.app/health`
  - Observed 2026-05-02: HTTP 200
  - JSON: `ok: true`, `role: "api"`, `allowLiveRuns: false`, `defaultModel: "deepseek-v4-flash"`

- Paperclip UI: `https://paperclip-server-production-b429.up.railway.app/`
  - Observed 2026-05-02: HTTP 200
  - Served Paperclip HTML app.

## Source mapping

- `paperclip-server` source repo in Railway: `engerlina/paperclip`, branch `master`.
- `hermes-api`, `hermes-worker`, and `hermes-scheduler` source repo in Railway status: `null`.

## Paperclip API/UI inventory

Unauthenticated safe reads found:

- `/api/health` returns JSON:
  - `status: ok`
  - `version: 0.3.1`
  - `deploymentMode: authenticated`
  - `deploymentExposure: private`
  - `authReady: true`
  - `bootstrapStatus: ready`
  - `bootstrapInviteActive: false`
  - `features.companyDeletionEnabled: false`
- `/api/skills/available` is public and returns Paperclip-managed skills:
  - `paperclip`
  - `paperclip-create-agent`
  - `paperclip-create-plugin`
  - `para-memory-files`

Authenticated endpoints return `403 Board access required`, which is expected for private deployment mode:

- `/api/companies`
- `/api/companies/stats`
- `/api/instance/scheduler-heartbeats`
- `/api/plugins`

The frontend bundle exposes a broad Paperclip API surface including companies, agents, agent hires/configurations, approvals, issues, routines, heartbeat runs, execution workspaces, costs, budgets, secrets, plugins, skills, and OpenClaw invite prompts.

Important endpoint families discovered from the frontend bundle:

- `/api/companies`
- `/api/companies/:id/agents`
- `/api/companies/:id/agent-configurations`
- `/api/companies/:id/agent-hires`
- `/api/companies/:id/budgets/overview`
- `/api/companies/:id/heartbeat-runs`
- `/api/companies/:id/live-runs`
- `/api/companies/:id/sidebar-badges`
- `/api/companies/:id/openclaw/invite-prompt`
- `/api/issues/:id/runs`
- `/api/heartbeat-runs/:id/log`
- `/api/instance/scheduler-heartbeats`
- `/api/skills/available`
- `/api/plugins`

## Log sample findings

- `paperclip-server` logs show active UI polling for company `live-runs` and `sidebar-badges` endpoints.
- `hermes-api` logs show it starts successfully and listens on `:8080`.
- `hermes-scheduler` logs show it schedules heartbeat runs approximately every 15 minutes.
- `hermes-worker` logs show it claims and finishes mock heartbeat runs with `exit=0`.

## Why it matters

This is currently the strongest running implementation of the desired architecture:

```text
Paperclip UI/control surface
  + Hermes API
  + Hermes scheduler
  + Hermes worker
  + Postgres state
```

It should be treated as the first Paperclip/Super-Agent runtime candidate.

## Current recommendation

Use this as the Paperclip/Hermes inspection target, but do not make it the single source of truth yet.

Primary Hermes should keep an independent portfolio registry so the framework survives even if Paperclip breaks.

## Approval rules

Requires Justin approval before:

- Redeploying.
- Restarting.
- Changing Railway variables.
- Scaling.
- Deleting services/databases.
- Enabling live runs.
- Running outbound workflows.

## Next read-only checks

1. Identify source repos for `hermes-api`, `hermes-worker`, and `hermes-scheduler`.
2. Inspect Paperclip companies and agent/team model through safe UI/API reads.
3. Map how Paperclip company IDs correspond to offers/businesses.
4. Determine whether Paperclip can be controlled programmatically by primary Hermes.
5. Decide whether each offer gets:
   - a Paperclip company,
   - a business CEO agent,
   - a budget/approval policy,
   - a heartbeat/reporting contract.
