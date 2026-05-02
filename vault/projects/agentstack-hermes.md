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
