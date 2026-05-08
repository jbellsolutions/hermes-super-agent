---
name: skool-dm
runtime: browser_use
tier: 2
category: social_action
cost_class: low
risk_class: medium
preferred_models: []
mcp_or_native: native
description: Send a private DM to a Skool group member. Navigates to the member's profile, opens the message thread, types the message, and sends. Includes verify step. Rate cap enforced from group config.
---

## When to use
- Sending welcome DM to a new member
- Sending outreach DM to a warm lead who is a Skool member
- Sending follow-up DM to a stalled JAP member
- Jobs tagged: `skool-dm`, `send-dm`, `message-member`

## When NOT to use
- Posting to the public feed → use `skool-post`
- Messaging leads on LinkedIn or Twitter → log for human follow-up (out of scope)
- Bulk broadcast (>25/day) → enforced by rate cap, will refuse

## How it works
1. Hermes routes job to `browser_use` runtime
2. `invoke.py` loads playbook: `src/agent_os/runtimes/browser_use/playbooks/skool/send-dm.yaml`
3. Playbook steps:
   a. Navigate to `config.group.skool_url`
   b. Login if needed (same credential flow as skool-post)
   c. Navigate to member profile (by username or member URL from job.metadata.member_url)
   d. Click "Message" button
   e. Type DM content (passed as job.prompt)
   f. Click "Send"
   g. **Verify**: confirm "Message sent" UI state appears
4. Check rate cap: increment today's DM counter in vault; refuse if > daily_outreach_target
5. Mark member as DM'd in `vault/data/<group>-members.md`
6. Log to `vault/runs/YYYY-MM-DD/engagement.md` or `recruiting.md` (caller's responsibility)

## Approval gate
- Tier 2 — DM preview shown with recipient name and message before sending
- Grace period: 5 seconds

## Cost & latency
- Browser session: ~20-40 seconds per DM
- No LLM cost for sending step

## Rate limiting
- Hard cap: `config.recruiting.daily_outreach_target` DMs per day per group
- Counter stored in: `vault/runs/YYYY-MM-DD/dm-counter.txt`
- If cap hit: log remaining recipients for next day, emit warning (not error)

## Examples
- "Send the welcome DM to member Sarah Chen who just joined"
  → `job.prompt = [welcome DM text]`, `job.metadata.member_url = [profile url]`
- "Send outreach DM to John Smith: [message]"
  → same pattern

## Configuration
- `SKOOL_EMAIL` / `SKOOL_PASSWORD` — from vault/secrets/skool-<group>.env
- `config.<group>.yaml → recruiting.daily_outreach_target` — hard DM cap
- `config.<group>.yaml → recruiting.welcome_dm_template` — template path

## Error handling
- Member profile not found: log error, skip (don't halt batch)
- Message button not available (privacy settings): log as "cannot DM", skip
- Rate cap hit: halt batch, log remaining recipients to try tomorrow
- CAPTCHA: emit PendingAction
- Login fails: emit PendingAction

## See also
- src/agent_os/runtimes/browser_use/playbooks/skool/send-dm.yaml
- vault/skills/active/skool-group-manager/welcome-dm.md
- examples/skool-group-manager/agent-briefs/engagement-agent.md
- examples/skool-group-manager/agent-briefs/recruiting-agent.md
