# Vault Sync Contract

_Last updated: 2026-05-02_

## Requirement

All meaningful Super Agent, Single Brain COO, Paperclip company, and project-agent conversations/actions must sync to both:

- Obsidian
- Notion

This is mandatory. Obsidian is the macro source-of-truth vault; Notion can be the business/operator-facing database/dashboard layer.

## Current local status

The default local Obsidian vault path was checked:

```text
/Users/home/Documents/Obsidian Vault
```

It did not exist, so the initial vault folder and first Super Agent operating-decision note were created.

## What must be logged

### Conversation summaries

Log at the end of meaningful sessions:

- user decisions
- assistant actions
- files changed
- deployments inspected
- credentials needed, never values
- next actions
- blockers

### Action records

Log every meaningful action:

- repo commit/push
- Railway/DigitalOcean inventory
- SSH attempt or access change
- service restart/redeploy/delete proposal or execution
- Paperclip company/team changes
- COO decisions
- model/tool routing decisions
- agent/profile creation

### Agent activity

Each persistent agent should write/report:

- heartbeat
- current task
- recent outputs
- errors/blockers
- costs/usage when available
- approval requests

## Obsidian structure

Recommended structure:

```text
Obsidian Vault/
  Super Agent/
    Decisions/
    Session Summaries/
    Deployment Health/
    Tool Routing/
  Single Brain COO/
    Decisions/
    Daily Reports/
    Weekly Reviews/
    Company Scorecards/
  Paperclip Companies/
    SDR Fleet/
    Expert Offer/
    Sovereign Offer/
    Zions/
  Projects/
  People/
  Vendors/
```

## Notion structure

Recommended synced databases:

- Conversations
- Actions
- Decisions
- Companies / Offers
- Agents
- Deployments
- Health Reports
- Approval Requests
- Costs

## Sync policy

- Obsidian gets durable narrative notes and markdown-friendly context.
- Notion gets structured database rows and operator dashboards.
- If only one can be updated in a moment, update Obsidian first and mark Notion sync pending.
- Never sync raw secrets.
- Use `[REDACTED]` for keys, tokens, env values, private URLs, or sensitive customer data.

## Agent profile rule

Separate Hermes profiles/agents may have isolated memory and secrets, but they should still roll up macro-level status to the shared vault.

Examples:

- Primary Hermes writes system/build/infra actions.
- Single Brain COO writes business decisions, scorecards, and operating cadence.
- Zions agent writes project-specific reports but shares high-level status to the macro vault.
- Paperclip company CEOs write company-level heartbeats and approval requests.

## First implementation steps

1. Create/confirm Obsidian vault path in `OBSIDIAN_VAULT_PATH`.
2. Add a Notion integration/database map once Notion token/database IDs are available.
3. Add a session-end summary template.
4. Add a cron or hook that summarizes recent Hermes sessions into Obsidian.
5. Add a Notion sync script/database writer.
6. Add per-agent heartbeat templates.
