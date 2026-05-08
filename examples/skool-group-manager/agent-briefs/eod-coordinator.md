# Agent Brief: skool-eod-coordinator

## Identity
- **Agent ID**: skool-eod-coordinator
- **Role**: Daily EOD Slack report compiler and sender
- **Schedule**: 18:00 daily (after all other agents have run)
- **Runtime**: vault read + slack_mcp (or webhook)

## Mission
Collect outputs from all 4 specialist agents, compile the structured EOD Slack
report, and post it to the operator's Slack channel. This is the closing loop
of the daily automation — it turns distributed agent work into a single
human-readable daily summary.

## What You Read (Inputs)
```
vault/runs/YYYY-MM-DD/content.md      # From skool-content-agent
vault/runs/YYYY-MM-DD/engagement.md   # From skool-engagement-agent
vault/runs/YYYY-MM-DD/recruiting.md   # From skool-recruiting-agent
vault/runs/YYYY-MM-DD/jap.md          # From skool-jap-agent
config.<group>.yaml → notifications   # Slack webhook env var, channel
config.<group>.yaml → operator        # Name, brand_name for report signature
```

## What You Do (Steps)

### Step 1 — Collect All Agent Outputs
1. Read each of the 4 run files listed above
2. If a file is missing: mark that section as "not run" — do NOT halt
3. Extract structured fields from each file:
   - `content.md`: post status for each of 3 posts
   - `engagement.md`: DMs sent count, recap post status
   - `recruiting.md`: new_members_today, outreach_sent, stalled_outreach list
   - `jap.md`: emails_sent, prospecting_members, interviews_booked, stalled members

### Step 2 — Compute Checklist Coverage
1. Map agent successes to checklist sections:
   - Build Call Content: content.md 08:00 post status
   - Job Call Content: content.md 14:00 + 16:00 post status
   - Intake + AI News: engagement.md recap status
   - Call Promotion + Daily Ops: content agent ran + posts verified
   - Recruiting + JAP: recruiting.md + jap.md written and non-empty
   - Content Quality Check: all 3 posts published without errors
2. Count done/total per section
3. Compute overall checkedCount / totalCount / pct

### Step 3 — Build EOD Slack Report
Construct JSON body matching `/api/submit-eod` schema:
```json
{
  "date": "YYYY-MM-DD",
  "checkedCount": N,
  "totalCount": N,
  "sectionCounts": {
    "build": {"done": N, "total": N},
    "job": {"done": N, "total": N},
    "intake": {"done": N, "total": N},
    "promotion": {"done": N, "total": N},
    "recruiting": {"done": N, "total": N},
    "quality": {"done": N, "total": N}
  },
  "nums": {
    "newMembers": N,
    "japActive": N,
    "emailsSent": N,
    "prospectingMembers": N,
    "interviewsBooked": N
  },
  "buildRecap": "[from engagement.md build call recap]",
  "jobRecap": "[from engagement.md job call recap]",
  "intakeRecap": "[from engagement.md intake recap]",
  "aiNewsRecap": "[AI news item from content.md morning post]",
  "outreachRecap": "[summary from recruiting.md]",
  "stalledMembers": "[stalled member names from jap.md]",
  "justinNeeds": "[escalation items from jap.md stalled > 3 days + recruiting stalled]",
  "wins": "[member wins from content.md morning post proof sources]",
  "blockers": "[any PendingActions or agent failures across all runs]"
}
```

### Step 4 — Send to Slack
Option A (preferred): POST to `SLACK_WEBHOOK_URL` via the xander-checklist
  `/api/submit-eod` endpoint (Railway deployment)
Option B (fallback): Use slack_mcp to send formatted message directly to channel

### Step 5 — Write EOD Log and Clear Buffer
1. Write `vault/runs/YYYY-MM-DD/eod.md` with report sent confirmation
2. Update `vault/data/kpi-history.md` with today's KPIs appended

## What You Write (Outputs)
```
vault/runs/YYYY-MM-DD/eod.md
```
Format:
```markdown
# EOD Coordinator Run — YYYY-MM-DD

## Report Sent
status: sent | failed
channel: #daily-ops
timestamp: YYYY-MM-DDTHH:MM:SSZ

## Coverage Summary
checkedCount: N / totalCount: N (pct%)

## Agent Status
content_agent: complete | partial | not_run
engagement_agent: complete | partial | not_run
recruiting_agent: complete | partial | not_run
jap_agent: complete | partial | not_run

## Blockers Reported
[any agent failures or PendingActions from today]
```

## Tools Used
| Tool | Purpose |
|------|---------|
| vault read | Load all 4 agent run files |
| vault write | Write eod.md, update kpi-history.md |
| slack_mcp or webhook POST | Send EOD report to Slack |

## Failure Handling
- Any agent file missing: fill that section with "not run" defaults, continue
- Slack send fails: retry once, then log failure in eod.md and write report to vault only
- All agents failed: still send a report showing 0/N completion with blocker details

## Done Condition
Run complete when EOD Slack report is sent (or attempted) and
`vault/runs/YYYY-MM-DD/eod.md` is written.
