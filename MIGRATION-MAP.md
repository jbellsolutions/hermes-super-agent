# Migration Map

How prior framework repos collapse into agent-os. **Old repos are pattern donors, not code sources.** Their best ideas become Hermes skill files, OpenClaw configs, or AGI-1 skill submissions — not code ports.

## Framework repos → contribution

| Source pattern | What it contributes | Where it lands in agent-os |
|---|---|---|
| Identity-pack frameworks | Identity packs (Morgan/Alex/Jordan + COO/Head of Ops/GTM templates) | `packages/orchestrator/config/identities/*.yaml` |
| Restart-on-failure agents | Restart-on-failure heuristics; Computer Use playbooks | `packages/upgrader/smoke/` (restart logic); `packages/runtimes/computer_use/playbooks/` |
| English-prompt → swarm architectures | Swarm architecture prompt patterns | `vault/skills/_templates/design-swarm.md` |
| Meta→CEO→Lead→Worker hierarchies | Hierarchical delegation pattern | `vault/skills/_templates/hierarchical-delegation.md` |
| Division-preset frameworks | Division presets (SDR / content / recruiting) | `packages/orchestrator/config/identities/divisions/*.yaml` |
| `agi-1` | **Stays whole** — vendored | `vendor/agi-1/` git submodule, auto-updated nightly |
| Codex-specific pattern repos | Codex-specific patterns | Fold into `vendor/agi-1` as additional skill files |
| Council deliberation engines | Council deliberation engine | `packages/quality/invocations/council.py` (generic engine) |
| Dashboard prototypes | Next.js dashboard base | `packages/dashboard/` (base) |
| Skill-template repos | Skill template patterns | `vault/skills/_templates/` |
| Heartbeat / MCP wiring repos | Heartbeat patterns + MCP wiring | `packages/orchestrator/config/heartbeat.yaml` + MCP server entries |

## Vertical app repos → consumers

Specific vertical apps (cold-email, content-engine, SDR fleet, recruiting, COO control rooms, etc.) stay in their own repos. They each get a `manifest.yaml` so the agent-os graph can see them, and they consume agent-os via the orchestrator/runtime APIs.

Onboard one at a time via `examples/<name>/` as scope arises. No big-bang migration.

## What does NOT migrate

- **Code.** No file from any old framework repo gets ported as code into agent-os. Ideas migrate; implementations are replaced by vendored OSS or thin adapters.
- **Multiple dashboards.** Pick one base, fold the others in. No three-dashboard monorepo.
- **AGI-1 reframing.** Its README repositioning ("skills called by Hermes" rather than "framework that runs on repos") happens upstream in `vendor/agi-1`. Its skills don't change.

## Status of old repos

Old framework repos stay live as references. After agent-os successfully runs one vertical app end-to-end, revisit archiving with a README pointer.
