# Project: coo-platform

## Type

Railway project / COO dashboard candidate.

## Deployment

- Provider: Railway
- Project: `coo-platform`
- Project ID: `dcf1326d-cd7f-47be-9286-adb5e2ff56e7`
- Environment: `production`
- Environment ID: `c00898e5-f839-4d1f-9be9-8ecbe10e1778`
- Services:
  - `console` — latest deployment `SUCCESS`
  - `Postgres` — latest deployment `SUCCESS`
- Public health URL: `https://console-production-8975.up.railway.app/api/health`
- Health result observed 2026-05-02: HTTP 200, `{ "ok": true, "service": "coo-console" }`

## Railway runtime notes

- `console` builder: Railpack.
- `console` start command: `npm run start --workspace @coo-platform/console`.
- `console` healthcheck path: `/api/health`.
- `console` replicas: `1`.
- `console` sleep application: `false`.
- `console` source repo in Railway status: `null`.
- Watch patterns suggest a monorepo layout:
  - `/apps/console/**`
  - `/packages/**`
  - `/package.json`
  - `/package-lock.json`

## Related repo inspected

Repo: `https://github.com/jbellsolutions/coo-agent`

That repo is documentation/setup-heavy, not the Railway app source itself. It defines the COO concept, rules, heartbeats, Mac Mini setup, Paperclip setup, MCP-first tool policy, and SDR monitoring playbooks.

## Why it matters

This likely maps to Justin's COO Agent / business-control-room concept. It may become the business-only COO specialist or inform the COO specialist operating contract.

## Current recommendation

Rebuild the COO as the new **Single Brain COO** rather than trusting this legacy Railway app.

Keep `coo-platform` running until a replacement is live and verified, then consider shutting it down to remove lingering Slack/chat confusion.

Primary Hermes remains Justin's everything-builder/hub. The rebuilt COO should be a business-only cofounder/operator that can later control Paperclip company teams.

Recommended hierarchy:

```text
Justin
  ├── Primary Hermes Super Agent — everything builder/hub/control plane
  └── COO Specialist — separate business-only chat/dashboard
        └── Paperclip company CEOs/teams per offer
```

## OpenClaw vs Hermes assessment

The inspected `coo-agent` repo did not contain `OpenClaw` references. It references `ClaudeClaw` as the Telegram bridge and Claude Code/Computer Use as the runtime.

Recommendation:

- Do not rebuild just to replace OpenClaw unless the live app actually depends on OpenClaw after source mapping.
- For the commercial Super Agent product, make Hermes the parent orchestrator/control plane.
- Keep Claude Code/Codex as coding runtimes.
- Keep ClaudeClaw/A0/Telegram-style bridges as optional access layers.
- If a COO component currently says “OpenClaw,” translate that role to “Hermes-managed runtime/worker” rather than a wholesale rewrite.

## Approval rules

Requires Justin approval before:

- Redeploying.
- Restarting.
- Changing env vars.
- Deleting services/database.
- Sending outbound messages.
- Promoting it to the primary business control plane.

## Next read-only checks

1. Find the actual source repo for the Railway `coo-platform` app, because Railway reports source repo as `null`.
2. Pull a small redacted app log sample if the console starts producing logs.
3. Inspect the UI manually/browser-side and capture what it actually supports.
4. Map the data model: companies, agents, tasks, heartbeats, approvals, costs.
5. Decide whether to adapt this app or rebuild a cleaner COO specialist on Hermes + Paperclip + portfolio registry.
