# Migration Map

How the 14+ existing framework repos collapse into agent-os. **Old repos are pattern donors, not code sources.** Their best ideas become Hermes skill files, OpenClaw configs, or AGI-1 skill submissions — not code ports.

## Framework repos → contribution

| Old repo | What it contributes | Where it lands in agent-os |
|---|---|---|
| `agent-core` | Identity packs (Morgan/Alex/Jordan + COO/Head of Ops/GTM templates) | `packages/orchestrator/config/identities/*.yaml` (converted from JSON) |
| `coo-agent` | Restart-on-failure heuristics; Computer Use playbooks | `packages/upgrader/smoke/` (restart logic); `packages/runtimes/computer_use/playbooks/` |
| `forge` | English-prompt → swarm architecture prompt patterns | `vault/skills/_templates/design-swarm.md` (a Hermes skill) |
| `agent-company` | Meta→CEO→Lead→Worker hierarchy | `vault/skills/_templates/hierarchical-delegation.md` (a Hermes skill) |
| `ultimate-agent-framework` | Division presets (SDR / content / recruiting) | `packages/orchestrator/config/identities/divisions/*.yaml` |
| `division-builder` | Same family — pick whichever is further along, archive the other | (same as above) |
| `agi-1` | **Stays whole** — vendored | `vendor/agi-1/` git submodule, auto-updated nightly |
| `agi-codex` | Codex-specific patterns | Fold into `vendor/agi-1` as additional skill files |
| `titans-of-direct-response-mastermind-council` | Council deliberation engine | `packages/quality/invocations/council.py` (generic engine; Titans copy stays in its own repo) |
| `***REMOVED***` | Next.js dashboard base (most recent, monorepo-shaped) | `packages/dashboard/` (base) |
| `coo-dashboard` | Dashboard widgets | `packages/dashboard/components/` (absorbed) |
| `operations-core` | Apply-to-X templates | `packages/dashboard/templates/` (absorbed) |
| `gstack-framework` | Skill template patterns | `vault/skills/_templates/` |
| `agentstack` / `agentstack-fleet-builder` | Skip — nearly empty | — |
| `ops-os` | Heartbeat patterns + Paperclip MCP wiring | `packages/orchestrator/config/heartbeat.yaml` + MCP server entries |
| `***REMOVED***` / `***REMOVED***` | Paperclip integration patterns | MCP entries |

## Vertical app repos → consumers

These stay in their own repos. They each get a `manifest.yaml` (so the agent-os graph can see them) and they consume agent-os via the orchestrator/runtime APIs.

| Old repo | Example onboard target |
|---|---|
| `cold-email-agent` / `***REMOVED***-cold-email` / `autonomous-sdr-agent` / `social-sdr` / `gtm-company` | `examples/sdr-fleet/` |
| `speakeragent-api` / `speakeragent-linkedin` / `speakeragent-ops` / `speakeragent-frontend` / `speakeragent-council` / `speakeragent-waitlist` / `linkedin-autopilot` / `tenxva-*` | `examples/content-engine/` |
| `***REMOVED***` / `coo-dashboard` / `coo-agent` (when not contributing patterns) | `examples/coo-control-room/` |
| `titans-*` (council outputs, GTM strategies) | Stay in their own repos; no migration; reference by manifest only |
| `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `***REMOVED***` / `Orgo-Computer-Use-Agents` / `UAIS-*` / `***REMOVED***` | One-by-one onboard via `examples/<name>/` as scope arises; no big-bang migration |

## What does NOT migrate

- **Code.** No file from any old framework repo gets ported as code into agent-os. Ideas migrate; implementations are replaced by vendored OSS or thin adapters.
- **Multiple dashboards.** Pick ***REMOVED***'s base, fold the others in. No three-dashboard monorepo.
- **AGI-1 reframing.** Its README repositioning ("skills called by Hermes" rather than "framework that runs on repos") happens upstream in `vendor/agi-1` — but nothing about its skills changes.

## Status of old repos

Per Justin's call: all 14 old framework repos **stay live** for now. After agent-os successfully runs one vertical app end-to-end (Stage 11), revisit the question of archiving with a README pointer.
