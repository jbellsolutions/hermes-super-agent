# Deployment Access: Railway and DigitalOcean

This runbook defines the safe way for a Hermes/Super Agent session to inspect Railway and DigitalOcean without leaking secrets or making destructive changes.

## Principle

Start read-only. Inventory first. Do not restart, redeploy, delete, scale, or mutate services until the operator explicitly approves the action and scope.

## What we need access for

- Discover what apps, droplets, workers, databases, and dashboards are actually running.
- Map each deployment to a GitHub repo/project/business.
- Identify dead, duplicated, or failing services.
- Document costs, regions, domains, and health checks.
- Decide which projects deserve their own specialist agents.

## Railway access

### Preferred setup

1. Install Railway CLI if missing:

```bash
brew install railway
# or
npm install -g @railway/cli
```

2. Authenticate interactively:

```bash
railway login
```

If using a token, store it in the user's secret manager or `~/.hermes/.env`, never in this repo:

```bash
RAILWAY_TOKEN=<token>
```

3. Read-only inventory commands:

```bash
railway whoami
railway project list
railway status
```

For each project/service, collect only metadata and redacted env names:

```bash
railway variables --json | python3 - <<'PY'
import json, sys
try:
    data=json.load(sys.stdin)
except Exception:
    data={}
for k in sorted(data):
    print(f'{k}=[REDACTED]')
PY
```

### Do not run without approval

- `railway up`
- `railway redeploy`
- `railway down`
- `railway delete`
- `railway variables set/delete`
- Any command that changes services, variables, domains, or deployments.

## DigitalOcean access

### Preferred setup

1. Install `doctl` if missing:

```bash
brew install doctl
```

2. Authenticate:

```bash
doctl auth init
```

If using a token, store it in the user's secret manager or `~/.hermes/.env`, never in this repo:

```bash
DIGITALOCEAN_ACCESS_TOKEN=<token>
```

3. Read-only inventory commands:

```bash
doctl account get
doctl compute droplet list
doctl apps list
doctl databases list
doctl kubernetes cluster list
doctl compute ssh-key list
doctl balance get
```

For each app/droplet, collect:

- Name.
- ID.
- Region.
- Size/plan.
- Status.
- Public IP/domain.
- Tags.
- Repo/source if visible.
- Monthly cost estimate if available.

### Do not run without approval

- `doctl compute droplet delete`
- `doctl compute droplet-action reboot/power-off/resize/rebuild`
- `doctl apps update/create/delete`
- `doctl databases delete`
- `doctl compute ssh-key delete`
- Any command that mutates infrastructure.

## SSH key discovery

Read-only local discovery:

```bash
ls -la ~/.ssh
ssh-add -l || true
```

If a droplet requires SSH, prefer `doctl compute ssh <droplet>` or `ssh -i ~/.ssh/<key> user@host` after confirming the host. Do not print private key contents.

## Output docs to write after inventory

- `docs/deployments-inventory.md` — all Railway/DigitalOcean resources, redacted.
- `vault/projects/<project>.md` — one page per business/project.
- `docs/portfolio-roadmap.md` — what to keep, fix, archive, or promote into specialist agents.

## Commercial standard

For customer deployments:

- One customer/workspace per isolated deployment boundary.
- Separate secrets.
- Separate vault/memory.
- Separate budget/cost cap.
- Explicit approval gates for production changes.
- Redacted deployment inventory committed to repo; secret values never committed.
