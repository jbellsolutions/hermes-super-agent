---
name: skool-post
runtime: browser_use
tier: 2
category: social_action
cost_class: low
risk_class: medium
preferred_models: []
mcp_or_native: native
description: Post content to a Skool group feed. Navigates to the group, opens the post editor, types content, and submits. Includes a verify step to confirm the post appears. All Skool credentials are read from vault/secrets.
---

## When to use
- Any agent needs to publish text content to the Skool group feed
- Jobs tagged: `skool-post`, `publish-to-skool`, `drop-post`
- After OpenSwarm or claude_subagents drafts post copy

## When NOT to use
- Sending a private message to a member → use `skool-dm`
- Scraping the member list or activity feed → use `skool-scrape-members`
- Posting to any platform other than Skool

## How it works
1. Hermes routes job to `browser_use` runtime
2. `invoke.py` loads playbook: `src/agent_os/runtimes/browser_use/playbooks/skool/post-to-feed.yaml`
3. Playbook steps:
   a. Navigate to `config.group.skool_url`
   b. If not logged in: use `SKOOL_EMAIL` + `SKOOL_PASSWORD` from env (loaded from `config.admin_credentials_key`)
   c. Click "Write a post..." editor
   d. Type post content (passed as job.prompt)
   e. Click "Post" button
   f. **Verify**: wait 3s, refresh feed, confirm post appears with matching first 50 chars
4. Write result to `vault/runs/YYYY-MM-DD/content.md`

## Approval gate
- Tier 2 — action preview shown with post content before submission
- Grace period: 5 seconds (content posts are recoverable, but still show preview)

## Cost & latency
- Browser session: ~15-30 seconds per post
- No LLM cost for the posting step itself (drafting is upstream)

## Examples
- "Post this morning FOMO content to ***REMOVED*** Skool group"
  → `job.prompt = [post text]`, `job.metadata.group_config = "config.***REMOVED***.yaml"`
- "Drop the 14:00 job leads post to Skool"
  → same pattern with afternoon post copy

## Configuration
- `SKOOL_EMAIL` — admin account email (from vault/secrets/skool-<group>.env)
- `SKOOL_PASSWORD` — admin account password (from vault/secrets/skool-<group>.env)
- `config.<group>.yaml → group.skool_url` — target group URL

## Error handling
- Login fails: emit PendingAction (credential issue — do not retry automatically)
- Post editor not found: emit PendingAction (Skool UI may have changed)
- CAPTCHA: emit PendingAction (never bypass)
- Verify fails (post not visible after 3s): log as "unconfirmed", do NOT retry (avoid duplicate posts)

## See also
- src/agent_os/runtimes/browser_use/playbooks/skool/post-to-feed.yaml
- vault/skills/active/skool-group-manager/skool-dm.md
- examples/skool-group-manager/agent-briefs/content-agent.md
