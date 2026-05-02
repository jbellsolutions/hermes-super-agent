# Builder Swarm Harness

_Last updated: 2026-05-02_

## Purpose

Add OpenAI Symphony-style harness engineering to the coding side of Super Agent without bloating the default runtime.

This is for the builder swarm: Codex/Claude/Hermes coding workers that implement repo tasks in isolated workspaces and return proof of work.

It is not the COO, not Paperclip, and not the business dashboard.

## Recommendation

- Adopt the harness pattern now.
- Keep Symphony itself optional.
- Do not make Symphony a default dependency until it proves useful in real coding workflows or becomes a clear commercial selling point.

## Where it fits

```text
Primary Hermes Super Agent
  ├── Portfolio/deployment registry
  ├── COO specialist and Paperclip business teams
  └── Builder Swarm Harness
        ├── WORKFLOW.md per repo
        ├── isolated task workspace
        ├── Codex/Claude coding run
        ├── tests/lint/build
        ├── PR or patch
        └── proof-of-work report
```

## Why this helps commercially

It gives the product a clean story:

> “Every customer repo can come with an agent execution harness. The Super Agent dispatches coding tasks to isolated workers, they follow the repo’s workflow contract, run tests, and return proof before anything lands.”

This is sellable without forcing every customer to run Symphony.

## Default behavior

For every serious repo, add a `WORKFLOW.md` or equivalent that tells coding agents:

- how to set up the repo
- how to run tests
- how to run lint/type checks
- how to start the app
- what files are protected
- what approval gates exist
- how to submit proof of work
- how to open or prepare a PR

## Optional Symphony path

Use Symphony or a Symphony-compatible runner when:

- Linear/GitHub issues become the formal engineering queue.
- There are 3+ concurrent coding agents.
- Target repos have tests/CI and workflow contracts.
- We want a commercial “engineering swarm” demo.

Do not use it when:

- The task is business strategy, operations, or deployment discovery.
- The repo lacks a reliable test/build harness.
- A single Codex/Claude/Hermes run is simpler.

## Worker contract

Every builder-swarm task should produce:

- task ID / source issue
- repo and branch/workspace
- files changed
- commands run
- test results
- known limitations
- approval needed, if any
- PR URL or patch summary

## Approval gates

- Read-only analysis: no approval required.
- Workspace-local edits: allowed once task is assigned.
- Push/PR: allowed if repo policy permits.
- Merge/deploy: requires explicit approval unless pre-authorized.
- Secret/env changes: always require explicit approval.
- Production data migrations: always require explicit approval.

## First implementation step

Add `templates/WORKFLOW.md` to Super Agent. Future installs can copy it into any repo that should be builder-swarm ready.
