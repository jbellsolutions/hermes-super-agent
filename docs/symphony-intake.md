# Symphony Intake

Source: <https://github.com/openai/symphony>

## Summary

Symphony turns project work into isolated autonomous implementation runs. It monitors a work tracker, creates per-issue workspaces, launches Codex app-server sessions, and expects in-repo workflow contracts.

OpenAI describes it as an engineering preview for trusted environments, not a hardened production control plane.

## What Symphony is good for

- Engineering work queues.
- Linear-driven issue execution.
- Isolated per-issue workspaces.
- Many concurrent Codex implementation runs.
- Proof-of-work oriented delivery: CI, PRs, reviews, walkthrough artifacts.
- Harness engineering discipline: repos designed so agents can safely test and verify.

## What Symphony is not

- A business dashboard.
- A customer/company control plane.
- A Paperclip replacement.
- A general-purpose workflow engine.
- A default dependency for Super Agent today.

## Fit with Super Agent

Symphony should be treated as a coding-runtime/control pattern:

```text
Primary Hermes Super Agent
  ├── portfolio/project registry
  ├── business and deployment reporting
  ├── approval gates
  └── Symphony-style engineering runner
        ├── reads Linear/GitHub issues
        ├── creates isolated workspaces
        ├── launches Codex
        └── returns proof of work
```

## Recommendation

Do not install Symphony as a default runtime yet.

Do adopt its ideas:

- Add `WORKFLOW.md` or equivalent to serious repos.
- Use isolated workspaces for agent coding tasks.
- Require proof of work before acceptance.
- Keep workflow policy versioned in the repo.
- Let primary Hermes manage work, not babysit every coding agent turn.

## When to promote

Promote Symphony or a Symphony-compatible runner when:

- Linear becomes the main source of engineering tasks.
- Super Agent needs 3+ concurrent Codex implementation runs.
- Target repos have tests, CI, and clear harnesses.
- We need repeatable coding-agent dispatch independent of Telegram chat.

## Implementation options

1. Use OpenAI's Elixir preview for evaluation only.
2. Implement the Symphony `SPEC.md` in Python inside Super Agent.
3. Add a thin adapter under `src/agent_os/runtimes/symphony/` that can call either implementation.

## First Super Agent task

Implemented first lightweight step:

```text
templates/WORKFLOW.md
docs/builder-swarm-harness.md
```

Use these for repos that want Symphony-style coding-agent execution. The template includes:

- tracker source
- workspace root
- setup hook
- test command
- approval policy
- PR/handoff instructions
- proof-of-work requirements
