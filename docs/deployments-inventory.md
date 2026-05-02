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
- Auth: token stored in `~/.hermes/.env`; read-only inventory commands run successfully by passing the token from env
- Account: `jbellsolutions@gmail.com`
- Team: `My Team`
- Droplet limit: `15`
- Month-to-date usage: `$5.04`
- Account balance: `$0.00`
- Inventory status: read-only droplet/app/database/kubernetes/SSH-key/project/balance list collected

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
  - Notes: strongest Railway candidate for current Paperclip/Hermes always-on agent stack.

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

## DigitalOcean inventory

DigitalOcean returned 8 active droplets, 0 App Platform apps, 0 managed databases, 0 Kubernetes clusters, 4 SSH keys, and 1 project.

### Droplets

- `ubuntu-s-2vcpu-4gb-nyc3-01`
  - ID: `555758742`
  - Status: `active`
  - Region: `nyc3`
  - Size: `s-2vcpu-4gb`
  - Public IP: `138.197.43.196`
  - Tags: none
  - Notes: generic name; needs SSH inspection/mapping.

- `LinkedinLeadGen`
  - ID: `557271278`
  - Status: `active`
  - Region: `nyc1`
  - Size: `s-1vcpu-1gb`
  - Public IP: `157.230.83.196`
  - Tags: none
  - Notes: likely lead-gen worker; candidate specialist/business service.

- `kevin-leads`
  - ID: `557997238`
  - Status: `active`
  - Region: `nyc1`
  - Size: `s-1vcpu-2gb`
  - Public IP: `157.230.95.186`
  - Tags: `kevin-leads`
  - Notes: likely customer/project-specific lead-gen box; isolate before touching.

- `cold-email-agent`
  - ID: `558001471`
  - Status: `active`
  - Region: `nyc1`
  - Size: `s-1vcpu-1gb`
  - Public IP: `134.122.17.43`
  - Tags: none
  - Notes: likely outbound/cold-email worker; high approval sensitivity.

- `yt-editor-pipeline`
  - ID: `561041593`
  - Status: `active`
  - Region: `nyc1`
  - Size: `s-1vcpu-2gb`
  - Public IP: `142.93.54.26`
  - Tags: none
  - Notes: content/video pipeline candidate.

- `paperclip-ops`
  - ID: `561064984`
  - Status: `active`
  - Region: `nyc1`
  - Size: `s-2vcpu-4gb`
  - Public IP: `167.172.131.251`
  - Tags: `paperclip`, `operations`
  - Notes: strongest DigitalOcean candidate for Paperclip operations/control-plane work.

- `removenews-ai-web`
  - ID: `562828031`
  - Status: `active`
  - Region: `nyc3`
  - Size: `s-1vcpu-2gb`
  - Public IP: `142.93.64.250`
  - Tags: none
  - Notes: web app/service candidate; map to repo/domain.

- `single-brain`
  - ID: `567676939`
  - Status: `active`
  - Region: `nyc3`
  - Size: `s-2vcpu-4gb-intel`
  - Public IP: `104.236.11.200`
  - Tags: `single-brain`
  - Notes: likely relevant to central-agent/single-brain experiments; inspect carefully.

### DigitalOcean App Platform

- No apps returned.

### DigitalOcean managed databases

- No managed databases returned.

### DigitalOcean Kubernetes

- No Kubernetes clusters returned.

### DigitalOcean SSH keys

- `cold-email-agent`
- `Claude Cowork Telegram Bot`
- `AI Lead Gen Mac 1`
- `Mac 2 SSH 1 Trading View Agent`

Fingerprints are available from `doctl compute ssh-key list` but omitted from this summary unless needed for SSH mapping.

### DigitalOcean projects

- `first-project`
  - Purpose: blank
  - Updated: `2026-02-04T16:18:23Z`

## First conclusions

1. Railway is carrying dashboards, app services, and several agent experiments.
2. DigitalOcean is carrying persistent worker/server droplets, including likely lead-gen, cold-email, content, Paperclip, and central-brain experiments.
3. `agentstack-hermes` on Railway and `paperclip-ops` on DigitalOcean are the two most important Paperclip/Super-Agent infrastructure candidates.
4. `coo-platform` on Railway may be worth testing, but should not become the main command center until it proves it can reliably report, execute, and respect approval gates.
5. `cold-email-agent` and lead-gen droplets must be treated with outbound-action approval gates.
6. Several duplicate/generated-name Railway projects likely need classification before cleanup.

## Read-only findings after first health pass

- Railway `coo-platform`:
  - `console` latest deployment: `SUCCESS`
  - Health URL: `https://console-production-8975.up.railway.app/api/health`
  - Observed result: HTTP 200, `ok: true`, `service: "coo-console"`
  - Start command: `npm run start --workspace @coo-platform/console`
  - Railway source repo: `null`, so source mapping is still needed.

- Railway `agentstack-hermes`:
  - `paperclip-server`, `hermes-api`, `hermes-worker`, and `hermes-scheduler` latest deployments: `SUCCESS`
  - Hermes API health: `https://hermes-api-production.up.railway.app/health`
  - Observed result: HTTP 200, `ok: true`, `role: "api"`, `allowLiveRuns: false`
  - Paperclip UI: `https://paperclip-server-production-b429.up.railway.app/`
  - Observed result: HTTP 200, Paperclip app HTML served
  - `paperclip-server` Railway source repo: `engerlina/paperclip`, branch `master`
  - Hermes service source repos still unmapped.

- DigitalOcean `paperclip-ops`:
  - SSH attempted as `root`, `ubuntu`, and `justin`.
  - Result: `Permission denied (publickey)`.
  - Local SSH agent has no loaded identities; local `~/.ssh/id_ed25519` was not accepted by this droplet.
  - No changes made.

## Next safe read-only steps

1. Find the actual source repo for Railway `coo-platform`.
2. Find source repos for Railway `agentstack-hermes` Hermes services.
3. Inspect Paperclip UI/API safely to map companies, offers, agents, runs, and heartbeat model.
4. Create the deployment health specialist report loop before COO/Paperclip autonomy.
5. Continue `paperclip-ops` only after the correct SSH key is available or approved.
6. Skip `single-brain` and `cold-email-agent` for now.
7. Do not delete, restart, redeploy, or mutate anything until Justin approves exact scope.
