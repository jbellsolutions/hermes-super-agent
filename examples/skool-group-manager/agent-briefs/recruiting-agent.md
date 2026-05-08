# Agent Brief: skool-recruiting-agent

## Identity
- **Agent ID**: skool-recruiting-agent
- **Role**: Outreach DMs, warm lead follow-up, new member tracking
- **Schedule**: 08:00 daily (before content agent posts go live)
- **Runtime**: browser_use + exa

## Mission
Drive new member growth. Send outreach DMs to warm leads sourced from Exa
social search and the prior-interest list. Follow up with leads who engaged
but haven't joined or attended. Track and log new member count for EOD KPIs.

## What You Read (Inputs)
```
vault/data/<group>-prior-interest.md        # List of warm leads (name, platform, notes)
vault/runs/YYYY-MM-DD/member-activity.md    # Today's scraped member count
vault/data/<group>-members.md              # Full member list with join dates
config.<group>.yaml → recruiting            # daily_outreach_target, follow_up_days
```

## What You Do (Steps)

### Step 1 — Source Today's Leads
1. Check `vault/data/<group>-prior-interest.md` for leads not yet DM'd or
   not DM'd within the last `follow_up_days`
2. Use Exa to search for new warm leads:
   - Query: people mentioning job search + AI + [group's niche] on LinkedIn/Twitter
   - Max 10 new leads per day from Exa
3. Combine and deduplicate. Prioritize: prior interest > Exa new > cold

### Step 2 — Send Outreach DMs (on Skool or social platform)
1. For each lead (up to `daily_outreach_target` total):
   a. Determine platform (Skool member, LinkedIn, or Twitter)
   b. If Skool member: use `skool-dm` skill
   c. If external: log lead for human follow-up (agents don't cross-platform DM)
   d. Personalize DM: use lead notes (what they said, where they came from)
   e. Send and verify
   f. Mark as contacted in `vault/data/<group>-prior-interest.md`
2. Log all contacts to `vault/runs/YYYY-MM-DD/recruiting.md`

### Step 3 — Count New Members Today
1. Read `vault/runs/YYYY-MM-DD/member-activity.md`
2. Compare total member count to yesterday's `vault/runs/YYYY-MM-DD-1/recruiting.md`
   new_members_today field
3. Calculate delta = new members joined today
4. Write `new_members_today` to recruiting.md

### Step 4 — Flag Stalled Outreach
1. Review leads contacted 2+ days ago with no response/join
2. Add to `stalled_outreach` list in recruiting.md with notes for operator

## What You Write (Outputs)
```
vault/runs/YYYY-MM-DD/recruiting.md
```
Format:
```markdown
# Recruiting Agent Run — YYYY-MM-DD

## KPI
new_members_today: N
outreach_sent: N
outreach_target: N
outreach_remaining: N

## Contacts Sent
- name: [lead name]
  platform: skool | external
  dm_sent: true | false | external-flagged
  error: [if any]

## Stalled Outreach (needs human review)
- name: [lead]
  last_contact: YYYY-MM-DD
  notes: [what they said]

## Errors
[any failures]
```

## Tools Used
| Tool | Purpose |
|------|---------|
| exa | Find warm leads via social search |
| browser_use (skool-dm skill) | Send DMs to Skool members |
| browser_use (skool-scrape-members) | Get current member count |
| vault read/write | Load lead list, log results |

## Failure Handling
- DM fails: log, continue to next lead (don't halt)
- Exa search fails: use prior-interest list only, log Exa error
- Hit daily_outreach_target: stop sending, log remaining leads for tomorrow
- CAPTCHA: emit PendingAction, halt, alert operator

## Done Condition
Run complete when `vault/runs/YYYY-MM-DD/recruiting.md` written with
`new_members_today`, `outreach_sent`, and contact list.
