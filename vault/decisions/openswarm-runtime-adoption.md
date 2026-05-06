# Decision: Adopt OpenSwarm as a specialist runtime + build the agent-builder agent on top of it

**Date:** 2026-05-05
**Status:** Accepted
**Affected components:** `src/agent_os/runtimes/openswarm/`, `src/agent_os/orchestrator/adapters/job_router.py`, `vendor/openswarm`, `ARCHITECTURE.md`, the upgrader (Phase C)

## Context

The super-agent stack already routes work to specialist runtimes when a job
shape calls for it. The gap so far: nothing in the stack produces
multi-deliverable artifacts well — slide decks, pitch packages, research
reports with embedded charts, executive summaries with one-pagers. Hermes
itself can write each piece, but quality drops on the integrated deliverable
because one agent can't keep slide design, research depth, chart aesthetics,
and copy tone all sharp at once.

[OpenSwarm](https://github.com/VRSEN/OpenSwarm) is a focused multi-agent
system that nails this exact gap: an orchestrator coordinates 7 specialists
(slides, deep_research, data_analyst, docs, video, image, virtual_assistant),
each tuned for one deliverable type. Built on agency-swarm, exposed as a
FastAPI server, MIT-licensed, vendorable.

We also want the **"build me an SEO swarm"** experience — what the OpenSwarm
launch video teases at the end but never ships. Each customized swarm should
be its own fleet member: own folder, own port, own .env, own manifest, own
vault attribution.

## Decision

1. **Vendor OpenSwarm** at `vendor/openswarm` (git submodule), upgrader stream
   pulls + smoke-tests nightly (Phase C).
2. **Adapter at `src/agent_os/runtimes/openswarm/`**, conforming to the
   existing `RuntimeResult` contract (`_base.py`). The runtime owns a
   **fleet** of forked OpenSwarm instances, not a single binary.
3. **Routing** via `build-swarm` / `multi-deliverable` / `swarm` tags plus
   per-swarm semantic match in `vault/skills/active/<name>-swarm.md` —
   builds grow Hermes' router automatically.
4. **Builder is the headline feature.** `op=build` forks vendor → swarm
   folder, runs a pluggable Customizer, hard-validates, and registers the
   skill atomically. Failures roll back to no partial state.
5. **Customizer is pluggable.** `claude_code` (default) shells out to the
   `claude` CLI in `--print` mode against the swarm folder; `manual` applies
   a deterministic spec without an LLM; `noop` for tests + the default
   swarm. Future `claude_subagents` runtime can plug in identically.
6. **Validator is pluggable.** `health` (default) boots the swarm + checks
   the FastAPI health endpoint; `smoke` adds a real LLM round-trip;
   `noop` skips for speed/tests.
7. **Multi-instance correctness is non-negotiable.** Per-swarm folder, port
   (allocated 8080–8099 with `bind` probe), `.env`, optional `.venv`,
   manifest, and run artifacts under `vault/runs/openswarm/<swarm>/`.

## Why a runtime adapter, not a Hermes plugin?

The first design draft was a `~/.hermes/plugins/openswarm/` plugin. That
ignored agent-os's existing seams: the runtime contract, the manifest
aggregator, the upgrader, the vault. Slotting in as
`src/agent_os/runtimes/openswarm/` means OpenSwarm gets the same lifecycle
guarantees as openclaw / browser-use / aider for free.

## Why default the customizer to `claude_code`?

`claude_code` matches what the OpenSwarm video shows: the user opens Cursor,
points it at `AGENTS.md`, and asks it to build an SEO swarm. We package that
flow inside Hermes — the user types one prompt to Hermes, Hermes shells out
to `claude --print --add-dir <swarm_dir>`, the LLM reshapes the clone, the
validator checks it boots, the skill gets rendered. End-to-end, no Cursor
required.

`manual` is the offline / deterministic / test-friendly customizer; future
work can add a `claude_subagents` customizer once that runtime is real.

## Consequences

- Each customized swarm grows the system's effective surface area. The router
  picks the right swarm by description-match; users don't manage which port
  to call.
- Fleet state lives outside the repo (`~/.agent-os/swarms/`), with the
  registry as single source of truth. Backup / migration is a flat YAML.
- Upgrade flow re-runs the customizer to reflow patches against new vendor
  HEAD; on conflict, it keeps last-known-good. Long-term, we expect the
  patches diff (captured by `claude_code`) to be the dominant replay path.
- New skills in `vault/skills/active/` mean Hermes router scoring against a
  growing list. Auto-deprecation after 90 days unused is a Phase D follow-up.

## Verification

- 65+ unit tests across registry, ports, http_client, fleet, builder,
  customizers, validators, invoke dispatcher, and routing rules — see
  `tests/unit/test_openswarm_runtime.py` and `tests/unit/test_job_router.py`.
- CLI smoke: `uv run agent-os route --tags build-swarm` returns
  `openswarm`; `uv run agent-os route --tags multi-deliverable` likewise.
- Phase A integration: `invoke({"op":"list"})` returns `RuntimeResult(status='ok')`
  even with an empty registry.
- Phase B integration: `invoke({"op":"build","name":"seo-swarm",
  "description":"SEO research and writing","customizer":"manual",
  "validator":"noop"})` produces a folder, a per-swarm manifest, a
  registry entry, and a vault skill. Failure injection at every step
  (customizer, validator, registry collision) rolls back atomically.

## Out of scope (for later phases)

- **Phase C** — upgrader stream `src/agent_os/upgrader/streams/openswarm.py`
  + smoke harness, idle hibernation, cost rollups in the dashboard.
- **Phase D** — cross-swarm handoff (slides from swarm A → docs in swarm B),
  parallel fan-out via Hermes subagents, channel-driven build (`/build-swarm`
  in Slack).
