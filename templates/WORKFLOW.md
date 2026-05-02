# WORKFLOW.md

This file tells coding agents how to work safely in this repository.

Copy this template into a project repo and fill in the blanks before assigning autonomous coding work.

## Repo identity

- Repo:
- Owner:
- Product/business:
- Primary human approver:
- Primary agent/orchestrator:

## Setup

```bash
# install dependencies
<command>
```

Required environment variables:

- `<NAME>` — purpose, where to obtain it, never commit value

## Common commands

```bash
# run tests
<command>

# run lint
<command>

# run type checks
<command>

# start local dev server
<command>

# build production artifact
<command>
```

## Protected areas

Agents must not edit these without explicit approval:

- `.env*`
- production deployment config
- database migrations
- billing/payment code
- customer data scripts
- authentication/authorization code
- generated assets unless requested

## Task workflow

1. Read the assigned task and this workflow file.
2. Inspect relevant files only; avoid broad context dumps.
3. Create or use an isolated branch/worktree.
4. Implement the smallest correct change.
5. Run the required checks.
6. Produce proof of work.
7. Prepare a PR or patch.
8. Do not merge or deploy without approval unless policy below allows it.

## Required proof of work

Every coding-agent result must include:

- task ID or source issue
- summary of change
- files changed
- commands run
- test/lint/build results
- screenshots or URLs if UI changed
- known limitations
- approval needed
- PR URL or patch location

## Approval policy

- Read-only inspection: allowed.
- Local workspace edits: allowed after task assignment.
- Push branch / open PR: allowed if credentials are configured.
- Merge to main: requires approval.
- Deploy production: requires approval.
- Change secrets/env vars: requires approval.
- Run database migrations: requires approval.
- Touch customer data: requires approval.

## Rollback

If a change breaks checks:

```bash
# show status
git status --short

# show diff
git diff

# revert local changes if instructed
git restore <path>
```

Document what failed and stop rather than stacking fixes blindly.

## Agent notes

- Prefer tests before implementation when feasible.
- Do not fabricate status; run checks fresh.
- Do not print secrets.
- Do not install global tools unless the workflow explicitly allows it.
- If blocked by missing credentials, say exactly which credential is missing and why it is needed.
