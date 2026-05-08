# Skool Group Manager — AI Agent Team

Fully automated AI agent team for managing a Skool community group.
Handles content posting, member engagement, recruiting outreach, JAP coaching,
and daily EOD Slack reporting — for any group via a single config file.

## What it does

Five specialist agents run on a daily schedule:

| Agent | Schedule | Owns |
|-------|----------|------|
| `skool-content-agent` | 08:00, 14:00, 16:00 | Morning FOMO post, job leads posts |
| `skool-engagement-agent` | Triggered | New member welcome DMs, call recap posts |
| `skool-recruiting-agent` | 08:00 | Outreach DMs, warm lead follow-ups |
| `skool-jap-agent` | 17:00 | Activity monitoring, KPI aggregation, stall detection |
| `skool-eod-coordinator` | 18:00 | Compile all outputs → Slack EOD report |

Human role reduces to: dropping call notes into vault, reviewing escalations, and filling config for new groups.

## Key constraint: Skool has no API

All Skool interactions go through `browser-use`. This is the primary fragility
point — CSS selectors can break on Skool UI updates. Every playbook includes a
verify step. CAPTCHA always escalates to human (PendingAction).

## Onboarding a new group (15 minutes)

1. Copy the config template:
   ```bash
   cp examples/skool-group-manager/config.template.yaml \
      examples/skool-group-manager/config.<group-slug>.yaml
   ```

2. Fill in the values in your new config file:
   - `group.name`, `group.skool_url`, `group.admin_credentials_key`
   - `operator.name`, `operator.brand_name`, `operator.slack_channel`
   - `calls.*` — your call schedule and platform
   - `content.post_voice` — paste 2-3 sentences describing the group's tone
   - `recruiting.daily_outreach_target` — how many DMs per day (default: 25)
   - `jap.stall_threshold_days` — days before flagging a member (default: 2)

3. Add Skool credentials to vault secrets:
   ```bash
   # Create vault/secrets/skool-<group-slug>.env (never commit this file)
   echo "SKOOL_EMAIL=admin@example.com" > vault/secrets/skool-<group-slug>.env
   echo "SKOOL_PASSWORD=yourpassword" >> vault/secrets/skool-<group-slug>.env
   ```

4. Activate via Hermes:
   ```
   "Activate the skool-group-manager for [group name] using config.[group-slug].yaml"
   ```

5. Hermes registers cron schedules, sets up vault watchers, and starts the
   first full run at 08:00 the next morning.

## Daily human workflow

| Time | Human action |
|------|-------------|
| After Build Call | Upload call notes to `vault/runs/YYYY-MM-DD/call-notes.md` |
| After Job Calls | Same — add job call highlights to call-notes.md |
| 18:00+ | Review EOD Slack report |
| Ongoing | Check Langfuse for any PendingAction alerts |

## Checking agent status

- **Langfuse**: full trace for every agent run
- **Vault**: `vault/runs/YYYY-MM-DD/` — one file per agent per day
- **Slack**: EOD report at 18:00 shows coverage and blockers

## Escalations to watch

The EOD report's `justinNeeds` field is auto-populated from:
- JAP members stalled > 3 days (from `jap.md`)
- Warm leads in stalled outreach > 5 days (from `recruiting.md`)
- Any PendingActions raised during the day

## File structure

```
examples/skool-group-manager/
├── manifest.yaml                    # Component declaration
├── config.template.yaml             # Per-group config template
├── config.ai-integrators.yaml       # AI Integrators instance config
├── README.md                        # This file
└── agent-briefs/
    ├── content-agent.md
    ├── engagement-agent.md
    ├── recruiting-agent.md
    ├── jap-coach-agent.md
    └── eod-coordinator.md

vault/skills/active/skool-group-manager/
├── skool-post.md                    # Hermes skill: post to feed
├── skool-dm.md                      # Hermes skill: send DM
├── skool-scrape-members.md          # Hermes skill: scrape members + activity
├── welcome-dm.md                    # Welcome DM template
└── orchestrate-daily-run.md         # Orchestration skill (ties all agents together)

src/agent_os/runtimes/browser_use/playbooks/skool/
├── post-to-feed.yaml                # browser-use: publish to Skool feed
├── send-dm.yaml                     # browser-use: send member DM
└── scrape-activity.yaml             # browser-use: scrape members + feed
```

## EOD report schema

The `skool-eod-coordinator` posts to the Slack webhook using the same schema
as the xander-checklist `/api/submit-eod` endpoint:

```json
{
  "date": "YYYY-MM-DD",
  "checkedCount": 18,
  "totalCount": 20,
  "sectionCounts": { "build": {...}, "job": {...}, ... },
  "nums": { "newMembers": 3, "japActive": 12, "emailsSent": 47, ... },
  "buildRecap": "...",
  "stalledMembers": "...",
  "justinNeeds": "...",
  "wins": "...",
  "blockers": "..."
}
```
