# Project: coo-platform

## Type

Railway project / COO dashboard candidate.

## Deployment

- Provider: Railway
- Project: `coo-platform`
- Environment: `production`
- Services:
  - `console`
  - `Postgres`

## Why it matters

This likely maps to Justin's COO Agent / business-control-room concept. It may become the business-only COO dashboard or a template for the COO specialist.

## Current status

- Discovered via read-only Railway inventory.
- Not yet service-inspected.
- No changes made.

## Current recommendation

Do not make this the main command center yet. Keep primary Hermes as Justin's everything-builder/hub. Test `coo-platform` as a business-only COO specialist/dashboard after reporting and approval gates are clear.

## Approval rules

Requires Justin approval before:

- Redeploying.
- Restarting.
- Changing env vars.
- Deleting services/database.
- Sending outbound messages.

## Next read-only checks

- Identify repo/source.
- Inspect logs/status.
- Determine if dashboard is reachable.
- Determine if it can produce daily business reports.
- Determine if it can be controlled programmatically by primary Hermes.
