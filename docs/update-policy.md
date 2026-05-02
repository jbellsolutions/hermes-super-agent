# Update Policy

Super Agent should improve daily, but stability beats novelty.

## Principles

1. **Document every new tool**: when a tool/runtime is added, update this repo in the same change.
2. **No silent breaking changes**: daily updates may check and stage upgrades, but they should not silently promote untested changes.
3. **Tests gate promotion**: an update is only promotable after smoke/unit checks pass.
4. **Prefer pull requests for upgrades**: automated upgrades should create a reviewable branch/PR instead of pushing directly to `main`.
5. **Keep secrets out**: update logs may name credential locations, but never include token/key values.
6. **Stable and consistent wins**: if a tool update fails checks or changes behavior unexpectedly, quarantine it and keep the known-good version.

## Required documentation for new tools

When adding a new tool, update the relevant files:

- `README.md` or `SUPER-AGENT.md` for the top-level role.
- `docs/super-agent-runtime.md` for runtime inventory.
- `src/agent_os/runtimes/<tool>/manifest.yaml` for runtime metadata, if the tool is part of routing.
- `src/agent_os/orchestrator/adapters/job_router.py` and tests if work should route to it.
- `docs/local-stack/` or `runbooks/` for local install/start/stop/health commands.
- `CHANGELOG.md` for the human-readable history.
- `vault/decisions/` for durable architecture decisions.

## Daily upgrade flow

Daily automation should:

1. Update/check Hermes and vendored tool streams.
2. Run each stream's smoke check.
3. Run repo quality gates:
   - `uv run ruff check src tests`
   - `uv run pytest tests/smoke tests/unit -q`
4. Write a dated log in `vault/upgrades/`.
5. Open or update an automated PR with passing changes.
6. Leave failed upgrades quarantined with the last stable version intact.

## Manual promotion checklist

Before merging an automated upgrade PR:

- [ ] Read `vault/upgrades/<date>.yaml`.
- [ ] Confirm CI passed.
- [ ] Confirm no secrets were added.
- [ ] Confirm Agent Zero/A0/Codex/Hermes local runbooks still match reality if affected.
- [ ] Merge only if the change is understandable and reversible.
