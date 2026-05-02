# Architecture

## The structural call

**Hermes is the persistent orchestrator. OpenClaw, browser-use, Aider, Codex, Claude Code, Computer Use, Claude Managed Agents, E2B, Exa, LiveKit, and Terminal are specialist runtimes Hermes routes to.** This is NOT a brain/arm split — Hermes can spawn its own sub-agent hierarchies and handle most work itself. The specialist runtimes earn their slot via pressure-tested community-velocity on specific surfaces.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            CHANNELS (single-state)                        │
│   Slack · Telegram · Web chat · Web voice (LiveKit + Realtime API) · CLI │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                ┌─────────────────────────────────────┐
                │   ORCHESTRATOR — Hermes (always-on) │
                │   memory · skills · sub-agents      │
                │   conversation · routing decisions  │
                └─────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────────────────┐
                │                   │                                │
                ▼                   ▼                                ▼
   ┌───────────────────┐  ┌──────────────────┐         ┌────────────────────┐
   │ SPECIALIST RUNTIMES│  │ QUALITY (agi-1) │         │ MANIFEST + EXPLAIN │
   │ • OpenClaw         │  │ • /agi-audit    │         │ • graph aggregator │
   │ • browser-use      │  │ • /agi-council  │         │ • MCP server       │
   │ • Computer Use     │  │ • /agi-research │         │ • /explain skill   │
   │ • Claude Code subs │  │ • genome        │         └────────────────────┘
   │ • Codex CLI        │  └──────────────────┘
   │ • Aider            │           │                            │
   │ • Claude Managed   │           ▼                            ▼
   │ • E2B sandboxes    │  ┌──────────────────────────────────────────────┐
   │ • Exa search       │  │              VAULT (markdown + Supabase)      │
   │ • LiveKit voice    │  │  conversations/ runs/ incidents/ skills/     │
   │ • Terminal         │  │  genome/ upgrades/ heartbeats/ graph/        │
   └───────────────────┘  └──────────────────────────────────────────────┘
                                    ▲
                                    │
                ┌─────────────────────────────────────┐
                │  UPGRADER (nightly cron, 10 streams) │
                │  pulls upstream → smoke → promote    │
                └─────────────────────────────────────┘
```

## How Hermes routes jobs

```
Job arrives at Hermes (Slack DM, schedule, sub-agent dispatch)
   │
   ├─ tags["coding","interactive"] OR repo edit  → Claude Code subagents
   ├─ tags["coding","background"] OR ["codex"]   → Codex CLI
   ├─ tags["coding","git-incremental"]           → Aider
   ├─ tags["browser","web-task","structured"]    → browser-use
   ├─ tags["autonomous-grind","shell","file-ops"]→ OpenClaw
   ├─ tags["raw-desktop","native-app"]           → Anthropic Computer Use
   ├─ tags["long-running","cloud"] OR >1hr est   → Claude Managed Agents
   ├─ tags["sandboxed-code","exec-untrusted"]    → E2B
   ├─ tags["search","articles","quick-lookup"]   → Exa
   ├─ tags["voice","realtime"]                   → LiveKit (handled at channel)
   ├─ tags["script","cron","simple"]             → Terminal
   └─ DEFAULT                                    → Hermes itself with sub-agents
```

The default is Hermes. Specialist runtimes are exceptions triggered by job type.

## The single-state guarantee

```
Every channel adapter is a thin shim. The agent (Hermes) lives ONCE.
Vault is the single source of truth for conversation memory.
Conversation identity is keyed to USER, not channel.
```

- `vault/conversations/<canonical_user_id>.md` — append-only conversation log indexed by user.
- File uploads from any channel → `vault/uploads/<sha>.ext`, path injected into Hermes' context.
- Hermes' memory adapter reads from + writes to the vault — every channel sees the same memory.

## The four "self-" pillars

### Self-healing (the concrete state machine)

```
Hermes heartbeat — every 5 min
│
├─ POLL: heartbeats, validators, cron schedule, API health, cost guardrails
├─ CLASSIFY: signature = (component, error_class, recent_changes_hash)
│            match against vault/genome/incidents.yaml
├─ KNOWN PATTERN → apply genome fix → verify → log → confidence++
├─ UNKNOWN     → 3-agent diagnostic council → propose fix
│              → if low-risk auto-apply, else PendingAction
│              → verify → log → if recurs 3+× promote to genome
└─ NIGHTLY 02:00:
       /agi-audit on day's outputs · score · regression check · journal
```

### Self-learning (Karpathy autoresearch shape)

```
Each run → vault/runs/<agent>/<ts>.yaml: prompt version, inputs, outputs,
                                          binary assertions, cost, latency
│
├─ Nightly rollup: pass-rate over last 30 runs · plateau or regression?
├─ If plateau → /agi-research:
│       generate 5 prompt variations · run on N test inputs in parallel
│       score against assertions + LLM-judge rubric
│       winner > incumbent by ≥5pp → PROMOTE → vault/skills/<agent>/SKILL.md
├─ Weekly: cross-project genome promotion (3+ project hits → genome)
└─ Quarterly: prune confidence < 0.6 OR unused 90+ days
```

### Self-growing (the upgrader's 10 streams)

The auto-update daemon runs nightly and pulls upstream. Each stream has its own smoke suite. Failures quarantine on a branch + Slack alert. See `packages/upgrader/streams/`.

| Stream | Source | What's tested in smoke |
|---|---|---|
| 1. Hermes | NousResearch/hermes-agent | boot, Slack listener, save-and-recall round-trip, Vault adapter, all promoted skills load |
| 2. OpenClaw | openclaw/openclaw | known shell sequence, browser auto on fixed page, output round-trip |
| 3. browser-use | browser-use/browser-use | nav + structured-extract + screenshot + shell-fallback trigger |
| 4. Aider | Aider-AI/aider | --version, fixture edit, passing test, commit message format |
| 5. Codex CLI | openai/codex (npm/pip pin) | --version, fixture compiles, output → vault/runs/ |
| 6. AGI-1 | jbellsolutions/agi-1 | /agi-audit on fixture, /agi-council completes, /agi-research promotes ≥1 |
| 7. awesome-hermes-agent | 0xNyk/awesome-hermes-agent | new skills → vault/skills/hermes-community/ as REVIEW-REQUIRED |
| 8. NemoClaw | NVIDIA/NemoClaw | **PARKED** until GA |
| 9. MCP registry | local + remote | new MCP servers auto-discovered + offered to Hermes as tools |
| 10. Vendor health | all submodules | verify each upstream is reachable, report stale-for-90+-days |

### Self-skills

- Hermes natively saves successful approaches as reusable skills (its headline feature) → `vault/skills/active/`.
- AGI-1 promotes high-confidence skills cross-project via `vault/genome/skills.yaml`.
- Community skills from `awesome-hermes-agent` land in `vault/skills/hermes-community/` as REVIEW-REQUIRED.
- Skills compound — your Brain literally has more abilities every week without you writing code.

## The introspection layer (answers "how do you all tie together?")

Every component writes a `manifest.yaml`:

```yaml
component: sdr-fleet
type: vertical-app
depends_on:
  agent-os.orchestrator: ">=0.1"
  agent-os.runtimes.openclaw: any
agents:
  - name: prospector
    role: "find leads in Apollo"
    tools: [apollo_mcp, vault]
    cost_budget_daily_usd: 5
data_sources: [apollo, smartlead, supabase.crm]
outputs:
  - type: email_send
    consumer: smartlead
upstream_signals: []
downstream_consumers: [coo-control-room]
```

`packages/manifest/aggregator.py` walks repos, builds `vault/graph/system.yaml`. The MCP server (`packages/manifest/mcp_server.py`) exposes the graph as queryable resources. The `/explain` skill walks it conversationally:

> *"How does the SDR fleet connect to the morning brief?"*
> → real graph walk, real answer.

## Accessibility (the most important section)

The thing that makes this genuinely better than "Claude Code with tools" is **persistent state across channels**. Drop a file in Slack, ask about it on Telegram, voice-chat about it from a web app — same agent, same conversation, same memory.

### Channels

| Channel | Mechanism |
|---|---|
| Slack | Hermes' built-in adapter + file-upload→vault handler |
| Telegram | Hermes' built-in adapter |
| Web text chat | `packages/webapp/` Next.js, WebSocket bridge to Hermes, streams tokens, drag-drop file |
| Web voice | LiveKit (transport) + OpenAI Realtime API (default) or Gemini Realtime API (configurable) |
| CLI | Hermes' built-in CLI |

### Voice path

```
Browser audio → WebRTC → LiveKit room → Voice agent worker (LiveKit Agents)
   → OpenAI Realtime / Gemini Realtime → text → Hermes (full memory)
   → text → Realtime synthesis → LiveKit → browser
```

Voice path joins the same Hermes pipeline as Slack/Telegram. Single-state guarantee preserved.

### Acceptance criteria

1. Send "remember 42" via Slack. Ask via Telegram. Voice-chat the same question. All return 42 with same context.
2. Drop a PDF in Slack. Ask about contents from web app voice mode. Right answer.
3. Web app text chat streams tokens.
4. Voice round-trip <2s on a clean connection.
5. One-command deploy stands up the full stack from a fresh checkout.

## Languages and tooling

- **Python** for orchestrator / runtimes / manifest / quality / upgrader / channels (server side) — uv workspace.
- **TypeScript** for webapp (Next.js) and dashboard — pnpm workspace.
- **Markdown** for vault (human-readable single source of truth).
- **YAML** for manifests, identities, configs, genome, graph.
