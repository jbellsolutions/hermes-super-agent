# CLAUDE.md — agent-os project rules

These rules apply to any Claude Code session running inside this repo. They override defaults.

## The unbreakable rules

1. **Never edit `vendor/`.** Submodules are vendored upstream OSS (Hermes, OpenClaw, browser-use, Aider, agi-1, awesome-hermes-agent, NemoClaw). Edits there break the auto-updater. If a change is needed: open an upstream PR, or wrap in `packages/`.

2. **Never start a new framework wrapper.** This repo exists because there were 14. Frustration → upstream issue or a thin adapter in `packages/runtimes/<name>/`. Read `ETHOS.md`.

3. **Single-state guarantee for channels.** Every channel adapter (`packages/channels/*`) writes conversation memory through Hermes' Vault adapter. No channel-local state. No per-channel side memory.

4. **Smoke tests are non-negotiable for the upgrader.** `packages/upgrader/streams/<name>.py` MUST have a smoke check before a promotion path is added. A bad upstream commit silently promoted is the only failure mode that takes the system down.

5. **Default to Hermes.** The router (`packages/orchestrator/adapters/job_router.py`) handles tagged jobs. Untagged → Hermes itself. Don't overengineer the routing.

6. **Markdown vault is the source of truth.** Human-readable in `vault/`. Supabase mirrors. Never make Supabase the primary.

## Code style

- Python 3.11+, ruff for lint, mypy for types, pytest for tests.
- TypeScript via pnpm workspace for `packages/webapp/` and `packages/dashboard/` only.
- No comments unless the WHY is non-obvious.
- Functions over classes when reasonable.

## Adopted-tool routing

When work matches one of the layer roles in `ECOSYSTEM-PLAYBOOK.md`, route to that runtime — don't reinvent. Examples:
- "Run shell automation for an hour" → OpenClaw runtime, not raw subprocess.
- "Browse and extract structured data" → browser-use runtime, not custom Playwright.
- "Generate code for a fixture" → Codex CLI / Aider / Claude Code subagents per job tag.
- "Look up 10 recent articles" → Exa runtime, not browser-use.

## When asking the agent-os system itself questions

Use the `/explain` skill (backed by `packages/manifest/explain.py`). It walks the system graph in `vault/graph/system.yaml`. If the answer isn't there, the manifest is incomplete — fix the manifest, not the explanation.

## What "done" looks like

- Tests pass: `uv run pytest`
- Lint passes: `uv run ruff check && uv run mypy packages/`
- Manifest aggregates: `uv run python -m agent_os.manifest.aggregator`
- Smoke green: `uv run pytest tests/smoke/`
- For UI changes: `pnpm -F webapp dev` and verified in browser.
