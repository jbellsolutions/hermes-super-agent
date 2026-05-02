# Project: agentstack-hermes

## Type

Railway project / Paperclip + Hermes stack candidate.

## Deployment

- Provider: Railway
- Project: `agentstack-hermes`
- Environment: `production`
- Services:
  - `paperclip-server`
  - `Postgres`
  - `hermes-worker`
  - `Postgres-ek7H`
  - `hermes-api`
  - `hermes-scheduler`

## Why it matters

This is the strongest Railway candidate for an existing always-on Paperclip/Hermes system. The service names suggest a control-plane server, worker, API, scheduler, and databases.

## Current status

- Discovered via read-only Railway inventory.
- Not yet service-inspected.
- No logs or env vars collected yet.
- No changes made.

## Approval rules

Requires Justin approval before:

- Redeploying.
- Restarting.
- Changing Railway variables.
- Scaling.
- Deleting services/databases.
- Running outbound workflows.

## Next read-only checks

- Link Railway project locally or inspect via CLI/API.
- Identify service source repos.
- Pull status/log summaries with secrets redacted.
- Determine public/internal URLs.
- Determine whether Paperclip API can provide company/agent heartbeat data to primary Hermes.
