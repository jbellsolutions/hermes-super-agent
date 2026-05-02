# Changelog

All notable changes to agent-os.

## [0.1.0] — 2026-04-29

### Added
- Initial scaffold of the unified agent-os repo.
- Architecture: Hermes (orchestrator) + specialist runtimes (OpenClaw, browser-use, Aider, Codex, Claude Code subagents, Anthropic Computer Use, Claude Managed Agents, E2B, Exa, LiveKit, Terminal) + agi-1 (quality) + Vault + Manifest + Upgrader + Channels + Webapp + Dashboard.
- Vendored upstream OSS as git submodules: hermes-agent, openclaw, nemoclaw (parked), browser-use, aider, awesome-hermes-agent, agi-1.
- Auto-updater daemon scaffolded with 10 nightly streams.
- Single-state accessibility layer: Slack + Telegram + web text + web voice → same Hermes instance.
- Self-healing state machine, self-learning autoresearch loop, self-growing upgrader, self-skills via Hermes' native skill saving + agi-1 promotion.
- `/explain` skill backed by manifest MCP server for system introspection.
- Deploy templates: Railway / Docker Compose / Fly.io.
- CI workflow with smoke + lint + type + unit gates.

### Notes
- NemoClaw integration wired but disabled — flip `UPGRADER_ENABLE_NEMOCLAW=true` once NVIDIA marks it GA.
- 14 old framework repos remain live per Justin's call. Revisit archive question after one vertical app onboards onto agent-os end-to-end.
## Super Agent conversion

- Rebased `hermes-super-agent` onto `jbellsolutions/agent-os` as the actual repo foundation.
- Added Super Agent identity, operating model, and runtime docs.
- Added Agent Zero + A0 as a documented runtime layer.
- Preserved prior Hermes/Codex/Agent Zero/A0 setup documentation under `docs/local-stack/`.
- Added `super-agent` CLI alias while keeping `agent-os` compatibility.

## Safe daily updates

- Added `docs/update-policy.md` with the rule that new tools must update the repo.
- Changed nightly upgrades to open a reviewable PR only after updater streams, Ruff, and smoke/unit tests pass.
- Kept the upgrade posture conservative: stable and consistent beats newest.

