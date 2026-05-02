# Deployment Health Specialist

_Last updated: 2026-05-02_

## Purpose

The first specialist-agent pilot should be a deployment health specialist, not a fully autonomous COO or Paperclip business CEO.

Why: the portfolio already has multiple Railway projects and DigitalOcean droplets. Before any COO or business-team autonomy can be trusted, the system needs a clean, current map of what exists, what is running, what is broken, what it costs, and which repo/business owns each deployment.

## Place in the hierarchy

```text
Justin
  └── Primary Hermes Super Agent
        ├── Deployment Health Specialist   ← first pilot
        ├── Business-only COO Specialist   ← second pilot
        └── Paperclip business teams       ← after registry/control plane works
```

The deployment health specialist reports to primary Hermes. It does not independently restart, redeploy, delete, scale, or run outbound workflows.

## Responsibilities

- Read-only Railway inventory.
- Read-only DigitalOcean inventory.
- Read-only health checks of known public endpoints.
- Read-only SSH inspection only when SSH keys are available and Justin approves the target.
- Deployment-to-repo mapping.
- Cost snapshot and drift detection.
- Broken/unknown deployment classification.
- Produce a daily/weekly health report for Justin via primary Hermes.

## Explicit non-responsibilities

- No deletes.
- No restarts.
- No redeploys.
- No variable changes.
- No database mutations.
- No outbound lead-gen/cold-email/campaign actions.
- No autonomous business decisions.

## Health report schema

```yaml
report_date: YYYY-MM-DD
scope:
  railway_projects_checked: []
  digitalocean_droplets_checked: []
summary:
  healthy: []
  warning: []
  critical: []
  unknown: []
costs:
  digitalocean_month_to_date: null
  railway_estimate: null
findings:
  - deployment: name
    provider: railway|digitalocean|other
    status: healthy|warning|critical|unknown
    evidence: command_or_url_checked
    owner_repo: unknown_or_url
    business_owner: unknown_or_name
    next_action: text
approval_needed:
  - action: text
    reason: text
```

## Current first targets

### P0

- Railway `coo-platform`
  - Public health: `https://console-production-8975.up.railway.app/api/health`
  - Current observed result: HTTP 200, JSON `{ ok: true, service: "coo-console" }`
  - Purpose: COO dashboard candidate.

- Railway `agentstack-hermes`
  - Public health: `https://hermes-api-production.up.railway.app/health`
  - Current observed result: HTTP 200, JSON with `ok: true`, `role: "api"`, `allowLiveRuns: false`, `defaultModel: "deepseek-v4-flash"`
  - Purpose: active Hermes/Paperclip stack candidate.

- Railway `agentstack-hermes` / `paperclip-server`
  - Public UI: `https://paperclip-server-production-b429.up.railway.app/`
  - Current observed result: HTTP 200, Paperclip HTML served.
  - Recent logs show active browser polling of company live-runs/sidebar badges.

- DigitalOcean `paperclip-ops`
  - Current observed result: SSH attempted as `root`, `ubuntu`, and `justin`; all returned `Permission denied (publickey)`.
  - Purpose: possible Paperclip operations droplet.

### Skip for now

- DigitalOcean `single-brain` — explicitly deprioritized.
- DigitalOcean `cold-email-agent` — explicitly deprioritized; outbound-action sensitive.

## SSH access finding

Local SSH agent currently has no loaded identities. `~/.ssh/id_ed25519` exists, but DigitalOcean `paperclip-ops` did not accept it for `root`, `ubuntu`, or `justin`.

Next options:

1. Add/load the matching private key for the `paperclip-ops` droplet.
2. Use DigitalOcean console to add an approved SSH key.
3. Skip droplet-level inspection until the Railway Paperclip stack is mapped.

No SSH changes were made.

## First pilot behavior

The first automated version should run in observe/report mode:

1. Query provider inventories.
2. Check approved public health endpoints.
3. Pull small, redacted log samples only when needed.
4. Compare with the last report.
5. Report unknown/broken/costly items to primary Hermes.
6. Ask for approval before any action.

## Promotion criteria

Promote from report-only to controlled execution only after:

- Every major deployment is mapped to a repo/business/owner.
- Health checks are stable for at least one week.
- Secrets redaction is proven.
- Approval gates are tested.
- Cost reporting is accurate enough for decisions.
