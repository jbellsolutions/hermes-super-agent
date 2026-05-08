---
name: orchestrate-skool-daily-run
runtime: hermes_self
tier: 2
category: orchestration
cost_class: medium
risk_class: low
preferred_models: [claude-sonnet-4-6]
mcp_or_native: native
description: Orchestrates the full daily agent run for a Skool group. Reads the group config, fires agents in schedule order, passes inter-agent outputs via vault/runs/YYYY-MM-DD/, handles individual agent failures gracefully, and triggers the EOD report at 18:00.
---

## When to use
- Daily cron trigger at 08:00 (kicks off content + recruiting agents)
- Manual invocation: "Run the Skool daily workflow for [group name]"
- Jobs tagged: `skool-daily`, `orchestrate-skool`, `run-group-manager`

## When NOT to use
- Running a single agent manually → invoke that agent's brief directly
- Setting up a new group for the first time → use Archon builder flow
- Fan-out across many groups simultaneously → use `coordinator` runtime

## How it works

### Phase 1 — 08:00 Morning Burst (parallel)
1. Load group config: `examples/skool-group-manager/config.<group>.yaml`
2. Run `skool-scrape-members` skill → writes `vault/runs/YYYY-MM-DD/member-activity.md`
3. In parallel (after scrape):
   - Dispatch `skool-content-agent` (morning post)
   - Dispatch `skool-recruiting-agent` (outreach DMs)
4. Dispatch `skool-engagement-agent` (new member welcome DMs) — reads member-activity.md

### Phase 2 — 14:00 and 16:00 Content Drops
5. Dispatch `skool-content-agent` with `run_id: afternoon-1` (14:00 job leads)
6. Dispatch `skool-content-agent` with `run_id: afternoon-2` (16:00 job leads)

### Phase 3 — Post-Call Engagement (event-driven)
7. When `vault/runs/YYYY-MM-DD/call-notes.md` is written (human uploads after call):
   - Dispatch `skool-engagement-agent` with trigger: `call-recap`

### Phase 4 — 17:00 JAP Review
8. Dispatch `skool-jap-agent`
9. Wait for `vault/runs/YYYY-MM-DD/jap.md` to be written

### Phase 5 — 18:00 EOD Report
10. Dispatch `skool-eod-coordinator`
11. Confirm `vault/runs/YYYY-MM-DD/eod.md` written and Slack report sent

## Failure handling
- Any individual agent fails: log failure, continue orchestration
- Scrape fails at Phase 1: engagement and recruiting use prior day's data
- EOD coordinator gets partial data: still sends report, marks missing sections
- Total run failure (all agents fail): send minimal Slack alert: "⚠️ Daily run failed — check vault/runs/YYYY-MM-DD/"

## Inter-agent data flow (vault-mediated)
```
skool-scrape-members ──→ vault/runs/YYYY-MM-DD/member-activity.md
                                │
                 ┌──────────────┼──────────────┐
                 ↓              ↓              ↓
        content-agent  engagement-agent  recruiting-agent
                 │              │              │
                 ↓              ↓              ↓
           content.md    engagement.md   recruiting.md
                 │              │              │
                 └──────────────┼──────────────┘
                                │
                          jap-agent
                                │
                            jap.md
                                │
                        eod-coordinator
                                │
                         Slack EOD report
```

## Examples
- "Run the Skool daily workflow for AI Integrators"
  → loads `config.ai-integrators.yaml`, executes full sequence
- "Manually trigger the EOD report for AI Integrators"
  → skips to Phase 5, reads whatever run files exist

## Configuration
- `config.<group>.yaml` — all group-specific settings
- `SLACK_WEBHOOK_URL` — for EOD report and failure alerts
- Agent schedules are set in `config.<group>.yaml → schedule.agents`

## Activation
Tell Hermes: *"Activate the skool-group-manager for [group name] using config.[group-name].yaml"*
Hermes will:
1. Load config
2. Register cron triggers for each schedule entry
3. Register vault watcher for call-notes.md (Phase 3 trigger)
4. Start daily run the next morning at 08:00

## See also
- examples/skool-group-manager/manifest.yaml
- examples/skool-group-manager/config.template.yaml
- examples/skool-group-manager/agent-briefs/
- vault/skills/active/skool-group-manager/
