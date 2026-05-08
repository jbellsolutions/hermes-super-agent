---
name: skool-scrape-members
runtime: browser_use
tier: 1
category: data_collection
cost_class: low
risk_class: low
preferred_models: []
mcp_or_native: native
description: Scrape the Skool group member list and activity feed. Extracts member names, join dates, last-active timestamps, and any application/activity posts visible in the feed. Writes structured output to vault for downstream agents to read.
---

## When to use
- Any agent needs an up-to-date member list (new joins, total count)
- JAP agent needs today's activity feed to detect stalled members
- Engagement agent needs new member names for welcome DMs
- Jobs tagged: `skool-scrape`, `member-list`, `scrape-activity`

## When NOT to use
- Posting content → use `skool-post`
- Sending DMs → use `skool-dm`
- When vault/runs/YYYY-MM-DD/member-activity.md is already fresh (< 2 hours old)

## How it works
1. Hermes routes job to `browser_use` runtime
2. `invoke.py` loads playbook: `src/agent_os/runtimes/browser_use/playbooks/skool/scrape-activity.yaml`
3. Playbook steps:
   a. Navigate to `config.group.skool_url`
   b. Login if needed
   c. **Member tab**: Navigate to Members section, scroll to load all visible members
      - Extract: display name, username, join date, level/role
      - Compare to `vault/data/<group>-members.md` — identify new joins (today)
   d. **Activity feed**: Navigate to group feed, scroll last 24 hours of posts
      - Extract: author, timestamp, any mentions of "applications", "emails", "interview", "booked"
      - Flag posts that look like JAP updates (job search activity)
   e. Write both datasets to vault
4. Update running member list in `vault/data/<group>-members.md`

## Output files
```
vault/runs/YYYY-MM-DD/member-activity.md
```
Format:
```markdown
# Member Activity Scrape — YYYY-MM-DD HH:MM

## Member Counts
total_members: N
new_members_today:
  - name: [display name]
    username: [skool username]
    join_date: YYYY-MM-DD
    profile_url: [url]

## Activity Feed (last 24h — JAP-relevant)
- author: [name]
  timestamp: YYYY-MM-DDTHH:MM
  type: jap_update | build_share | question | other
  content_summary: [brief]
  application_count_mentioned: N | null

## Scrape metadata
scraped_at: YYYY-MM-DDTHH:MM:SSZ
pages_scrolled: N
oldest_post_captured: YYYY-MM-DDTHH:MM
```

## Cost & latency
- Browser session: 60-120 seconds (depends on group size)
- Runs once per day per group (or on demand)
- No LLM cost

## Configuration
- `SKOOL_EMAIL` / `SKOOL_PASSWORD` — from vault/secrets/skool-<group>.env
- `config.<group>.yaml → group.skool_url` — target group
- `config.<group>.yaml → vault.member_log_path` — where to update running member list

## Error handling
- Login fails: emit PendingAction
- Member tab fails to load: retry once after 10s, then log partial data
- Activity feed cut short (infinite scroll issue): log how far scrape reached, continue
- CAPTCHA: emit PendingAction

## See also
- src/agent_os/runtimes/browser_use/playbooks/skool/scrape-activity.yaml
- examples/skool-group-manager/agent-briefs/jap-coach-agent.md
- examples/skool-group-manager/agent-briefs/engagement-agent.md
- examples/skool-group-manager/agent-briefs/recruiting-agent.md
