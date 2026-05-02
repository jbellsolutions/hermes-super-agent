# Contributing

## The two unbreakable rules

1. **Don't edit `vendor/`.** PRs that touch vendored submodules will be closed. Send those upstream.
2. **Don't add another framework wrapper.** New ideas go into a runtime adapter (`packages/runtimes/<name>/`), a Hermes skill (`vault/skills/`), or an upstream contribution.

## Setup

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/agent-os.git
cd agent-os
uv sync
pnpm install
cp .env.example .env  # fill in keys
```

## Running tests

```bash
uv run pytest                      # all tests
uv run pytest tests/smoke/         # smoke
uv run ruff check                  # lint
uv run mypy packages/              # types
pnpm -r test                       # JS tests
```

## Adding a new specialist runtime

1. `packages/runtimes/<name>/` directory with `__init__.py`, `invoke.py`, `outputs.py`, `manifest.yaml`, `README.md`.
2. Add to `packages/orchestrator/adapters/job_router.py` — one new tag-match rule.
3. Add to `packages/upgrader/streams/<name>.py` if vendored — include smoke fixture.
4. Update `ECOSYSTEM-PLAYBOOK.md` + `ARCHITECTURE.md` routing diagram.
5. Tests in `tests/integration/runtimes/test_<name>.py`.

## Adding a new channel

1. `packages/channels/<name>/` directory.
2. MUST write conversation memory through Hermes' Vault adapter — never local state.
3. MUST resolve user identity to the canonical conversation log in `vault/conversations/<user_id>.md`.
4. Add to deploy templates (`deploy/`).

## The PR bar

- Tests added or amended.
- `ruff check` passes.
- `mypy packages/` passes.
- If touching the upgrader: a smoke fixture is included.
- If touching channels: the single-state guarantee tests pass (`tests/integration/channels/test_single_state.py`).
