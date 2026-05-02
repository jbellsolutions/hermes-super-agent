# Cursor SDK Intake

_Last updated: 2026-05-02_

Source: <https://cursor.com/blog/typescript-sdk>

## Summary

Cursor released a public-beta TypeScript SDK for programmatic agents:

```bash
npm install @cursor/sdk
```

Package checked:

- NPM: `@cursor/sdk`
- Latest observed version: `1.0.12`
- Description: TypeScript SDK for Cursor agents.

The SDK exposes the same Cursor agent runtime used by Cursor desktop, CLI, web app, and Cloud Agents. It can run locally, on Cursor cloud, or on self-hosted workers.

## Why it matters to Super Agent

This is not “just another model.” It is a coding-agent runtime/harness layer.

It gives Super Agent another builder-swarm backend alongside:

- Codex CLI / Codex cloud-style runners
- Claude Code
- OpenClaw
- OpenCode
- Hermes subagents
- Symphony-style work-item harnessing

The commercial value is strong because Cursor is already trusted by developers, and the SDK story is easy to sell:

> “The Super Agent can dispatch coding tasks to the same agent runtime developers use inside Cursor, with cloud VMs, PR creation, MCP, skills, hooks, and subagents.”

## Capabilities from the announcement

- TypeScript API for creating agents and sending prompts.
- Local runtime against a working directory.
- Cloud runtime against dedicated VMs.
- Repo clone and configured dev environment in cloud.
- Stream events and reconnect later.
- Auto-create PRs, push branches, attach demos/screenshots.
- Agents show up in Cursor Agents Window and web app.
- Self-hosted workers for private networks.
- Codebase indexing, semantic search, and grep.
- MCP support via `.cursor/mcp.json` or inline config.
- Skills from `.cursor/skills/`.
- Hooks from `.cursor/hooks.json`.
- Subagents with named prompts/models.
- Model selection including `gpt-5.5`, Cursor Composer models, and other Cursor-supported models.

## How it should fit

Cursor SDK should be a **builder swarm tool**, not the COO, not the dashboard, and not the primary Super Agent brain.

```text
Primary Hermes Super Agent
  ├── Tool/router brain
  ├── Portfolio/deployment registry
  ├── COO / Paperclip business layer
  └── Builder Swarm
        ├── Codex backend
        ├── Claude Code backend
        ├── Cursor SDK backend
        ├── OpenClaw backend
        └── Symphony-style harness contract
```

Symphony is the harness concept: work item, isolated workspace, proof, PR/review.

Cursor SDK is one execution backend that can satisfy that harness.

## Recommended orchestration contract

Create a neutral “builder task” interface so the system does not become a pile of one-off tools:

```yaml
builder_task:
  id: string
  repo_url: string
  starting_ref: string
  task: string
  workflow_file: WORKFLOW.md
  runtime: cursor|codex|claude_code|openclaw|hermes
  model_policy:
    default: gpt-5.5
    cheap: deepseek
    specialized: composer-2
  sandbox: local|cloud|self_hosted
  allowed_actions:
    push_branch: true
    open_pr: true
    deploy: false
  proof_required:
    - tests
    - diff_summary
    - pr_url_or_patch
    - logs
```

## Runtime selection

### Use Cursor SDK when

- You want cloud coding agents with dedicated VMs and PR creation.
- The repo is TypeScript/JS-heavy or Cursor indexing gives a strong advantage.
- You want work visible in Cursor's Agents Window/web UI.
- You need MCP/skills/hooks/subagents in Cursor's ecosystem.
- The task is a commercial/customer-facing engineering swarm demo.

### Use Codex when

- OpenAI Codex is already authenticated and reliable.
- You want GPT-5.5 via OpenAI/Codex flow.
- You want local CLI/worktree execution.
- You want low integration overhead today.

### Use Claude Code when

- The project already has Claude Code instructions/skills.
- You want Anthropic tool behavior or existing Claude Code workflows.

### Use OpenClaw when

- The task benefits from OpenClaw-specific runtime behavior or existing OpenClaw-compatible setup.
- It is already wired into a customer/project and working.

### Use DeepSeek / cheap models when

- The task is repetitive, low-risk, or mostly mechanical.
- The repo has strong tests and the harness can catch failures.
- Cost matters more than maximum reasoning.

### Use GPT-5.5 / frontier models when

- Architecture/design risk is high.
- The task spans many files/systems.
- The repo has weak tests and the agent must reason more.
- Security, infra, auth, billing, or data migration is involved.

## Cursor SDK + Symphony harness

Best productized story:

```text
Super Agent Builder Swarm
  = Symphony-style harness
  + Cursor SDK backend
  + Codex backend
  + Claude Code backend
  + model/cost router
  + proof-of-work gate
```

This makes the marketplace story coherent:

- Tools are not random.
- Each tool is a backend behind a shared contract.
- Customers choose policies: cheapest, fastest, strongest, local-only, cloud-isolated.
- Super Agent owns routing, proof, approvals, and reporting.

## Recommendation

Add Cursor SDK as an optional Pro/Enterprise builder backend.

Do not make it a default dependency yet.

First implementation should be documentation + template only:

- Document the runtime selection matrix.
- Add `.cursor/` templates later.
- Add a small proof-of-concept only after `CURSOR_API_KEY` is available.
- Keep the neutral `WORKFLOW.md` contract so Codex, Claude Code, Cursor, and OpenClaw can all run the same task shape.

## Needed before live integration

- `CURSOR_API_KEY`
- Decision on allowed billing/cost cap for Cursor cloud agents.
- One test repo with good `WORKFLOW.md`.
- Policy for whether Cursor agents may auto-open PRs.
- Decision on local vs cloud vs self-hosted Cursor workers.

## First POC

Use a non-production repo and ask Cursor SDK to:

1. Summarize the repo.
2. Run tests/read the workflow.
3. Make a tiny docs-only change.
4. Open or prepare a PR.
5. Return proof of work.

If it succeeds, promote Cursor SDK to a supported builder backend.
