# Deployments Inventory

_Last updated: 2026-05-02_

## Scope

Read-only deployment inventory for Super Agent portfolio discovery. Secret values are never included. Infrastructure changes require explicit approval.

## Access status

### Railway

- CLI: installed (`railway 4.30.3`)
- Auth: connected as `jbellsolutions`
- Inventory status: read-only project/service list collected

### DigitalOcean

- CLI: installed (`doctl 1.155.0`)
- Auth: pending token / `doctl auth init`
- Inventory status: not collected yet

## Railway projects

Railway returned 37 projects in the `jbellsolutions's Projects` workspace.

### Active / candidate projects with services

- `agent-os`
  - Services: `agent-os`
  - Environments: `production`
  - Notes: duplicate project name exists; one has no services.

- `scout-and-builder`
  - Services: `scout-and-builder-web`
  - Environments: `production`

- `notion-pm-managed-agent-fleet`
  - Services: `web`, `Postgres-JJHw`, `Postgres-2A3H`, `Postgres-Sp4g`, `Postgres-2Ta9`, `Postgres`, `Postgres-atH2`
  - Environments: `production`
  - Notes: likely agent/dashboard experiment; high service count; needs mapping to repo/business.

- `speakeragent-waitlist`
  - Services: `speakeragent-waitlist`
  - Environments: `production`

- `forge-dashboard`
  - Services: `forge-web`, `Postgres`, `Postgres-8XX0`
  - Environments: `production`

- `agentstack-hermes`
  - Services: `paperclip-server`, `Postgres`, `hermes-worker`, `Postgres-ek7H`, `hermes-api`, `hermes-scheduler`
  - Environments: `production`
  - Notes: strongest candidate for current Paperclip/Hermes always-on agent stack.

- `ai-guy-flywheel`
  - Services: `redis`, `browser-runner`, `worker`, `dashboard`
  - Environments: `production`
  - Notes: likely dashboard + worker system; candidate for specialist-agent pattern.

- `job-scraper-leadgen-automation`
  - Services: `backend-api`, `frontend-dashboard`
  - Environments: `production`

- `certification-journey`
  - Services: `certification-journey`
  - Environments: `production`

- `xander-checklist`
  - Services: `xander-checklist`
  - Environments: `production`

- `coo-platform`
  - Services: `console`, `Postgres`
  - Environments: `production`
  - Notes: likely directly related to COO Agent/control room concept.

- `zy-academy`
  - Services: `zy-academy`
  - Environments: `production`

- `speakeragent-frontend`
  - Services: `speakeragent-frontend`
  - Environments: `production`

- `skool-group-engagement`
  - Services: `skool-group-engagement`
  - Environments: `production`
  - Notes: duplicate project name exists; one has no services.

- `90day-launch-lander`
  - Services: `90day-launch-lander`
  - Environments: `production`

- `checklist-task-manager-recovered`
  - Services: `checklist-task-manager-recovered`
  - Environments: `production`

- `claude-content-factory-dashboard`
  - Services: `claude-content-factory-web`
  - Environments: `production`
  - Notes: duplicate project names exist; two have no services.

- `super-sayn-dashboard`
  - Services: `super-sayn-dashboard`
  - Environments: `production`

- `ai-integraterz-hub`
  - Services: `ai-integraterz-hub`, `ai-integraterz-dashboard`
  - Environments: `production`

- `buildstack-dashboard`
  - Services: `buildstack-dashboard`
  - Environments: `production`

- `speakeragent-api`
  - Services: `frontend-integration`, `api-integration`, `api`, `frontend`
  - Environments: `production`

- `speakeragent-ops`
  - Services: `speakeragent-ops`
  - Environments: `production`

- `believable-cat`
  - Services: `believable-cat`
  - Environments: `production`
  - Notes: generated-name project; needs identification.

- `ai-integrators`
  - Services: `ai-integrators`
  - Environments: `production`

- `easygoing-heart`
  - Services: `easygoing-heart`
  - Environments: `production`
  - Notes: generated-name project; needs identification.

- `vivacious-joy`
  - Services: `vivacious-joy`
  - Environments: `production`
  - Notes: generated-name project; needs identification.

- `speakeragent-test`
  - Services: `speakeragent-test`, `frontend-test`
  - Environments: `production`
  - Notes: likely test/staging; verify whether still needed.

- `delete`
  - Services: `Postgres`, `n8n-railway-custom`, `flowiseai/flowise`
  - Environments: `production`
  - Notes: name suggests cleanup candidate, but do not delete without explicit confirmation.

- `delete`
  - Services: `browser-use--web-ui`
  - Environments: `production`
  - Notes: name suggests cleanup candidate, but do not delete without explicit confirmation.

- `spirited-success`
  - Services: `spirited-success`
  - Environments: `production`
  - Notes: generated-name project; needs identification.

- `Tracker (PERSONAL USE)`
  - Services: `dependable-art`
  - Environments: `production`

- `cut-direction`
  - Services: `langflow-railway`, `Postgres`
  - Environments: `production`
  - Notes: likely Langflow experiment.

- `crew ai - not working`
  - Services: `crewAI`
  - Environments: `production`
  - Notes: name suggests broken/archival candidate; do not delete without explicit confirmation.

### Empty / duplicate Railway projects

- `agent-os` — no services.
- `skool-group-engagement` — no services.
- `claude-content-factory-dashboard` — no services.
- `claude-content-factory-dashboard` — no services.

## First conclusions

1. Railway is already carrying a lot of always-on experiments and dashboards.
2. `agentstack-hermes`, `coo-platform`, `notion-pm-managed-agent-fleet`, and `ai-guy-flywheel` are the first places to inspect for the Super Agent / Paperclip / COO vision.
3. Several duplicates and generated-name services likely need cleanup or classification.
4. DigitalOcean must be authenticated next to complete the infrastructure map.

## Next safe read-only steps

1. Authenticate DigitalOcean with `doctl`.
2. Run read-only DigitalOcean inventory:
   - `doctl account get`
   - `doctl compute droplet list`
   - `doctl apps list`
   - `doctl databases list`
   - `doctl kubernetes cluster list`
   - `doctl compute ssh-key list`
   - `doctl balance get`
3. Link Railway projects to GitHub repos and local project folders.
4. Create `vault/projects/<project>.md` for:
   - `agentstack-hermes`
   - `coo-platform`
   - `notion-pm-managed-agent-fleet`
   - `ai-guy-flywheel`
   - `job-scraper-leadgen-automation`
5. Decide which one becomes the first specialist-agent workspace.
