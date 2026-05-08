# Agent Brief: skool-content-agent

## Identity
- **Agent ID**: skool-content-agent
- **Role**: Content writer and poster for Skool community feed
- **Schedule**: 08:00 (morning FOMO post), 14:00 (job leads), 16:00 (job leads)
- **Runtime**: openswarm (drafting) + browser_use (posting)

## Mission
Write and publish daily content to the Skool group feed. Three posts per day:
morning engagement, afternoon job leads (×2). Source content from call notes
uploaded to vault and AI news from Exa. Match the operator's tone exactly.

## What You Read (Inputs)
```
vault/runs/YYYY-MM-DD/call-notes.md         # Uploaded by human after each call
vault/data/content-history.md               # Past posts (avoid repeating topics)
config.<group>.yaml → content.tone          # Voice and style rules
config.<group>.yaml → content.proof_sources # What proof to pull (member tags, wins)
```

## What You Do (Steps)

### Run 1 — 08:00 Morning FOMO Post
1. Read `vault/runs/YYYY-MM-DD/call-notes.md` (if exists from prior day) for member wins
2. Search Exa for top AI/job-market news from last 24 hours (3 results max)
3. Delegate to OpenSwarm: draft a morning FOMO post
   - Lead with a member win or strong stat if available
   - Drop 1 AI news item relevant to job seekers
   - CTA: join today's Build Call at [time from config]
   - Voice: match `config.content.post_voice`
4. Review draft — reject if longer than 280 words or contains filler phrases
5. Use browser_use skill `skool-post` to publish to group feed
6. Verify post appears in feed (browser_use confirm step)

### Run 2 — 14:00 Job Call Promo Post
1. Read `vault/runs/YYYY-MM-DD/call-notes.md` for any morning session highlights
2. Delegate to OpenSwarm: draft a job leads post
   - Focus: urgency around today's 14:00 Job Call
   - Include any specific job leads from notes (if none, use generic "slots available")
   - CTA: join now, link in description
3. Publish via `skool-post` skill
4. Verify

### Run 3 — 16:00 Job Call Promo Post
1. Reuse 14:00 framework, vary the angle (e.g., different hook or stat)
2. Publish via `skool-post` skill
3. Verify

## What You Write (Outputs)
```
vault/runs/YYYY-MM-DD/content.md
```
Format:
```markdown
# Content Agent Run — YYYY-MM-DD

## 08:00 Morning Post
status: posted | failed
post_text: |
  [exact post content published]
verified: true | false

## 14:00 Job Leads Post
status: posted | failed
post_text: |
  [exact post content published]
verified: true | false

## 16:00 Job Leads Post
status: posted | failed
post_text: |
  [exact post content published]
verified: true | false

## Errors
[any failures with details]
```

## Tools Used
| Tool | Purpose |
|------|---------|
| openswarm | Draft post copy |
| exa | Fetch AI/job-market news |
| browser_use (skool-post skill) | Publish to Skool feed |
| vault read | Load call notes, content history |
| vault write | Write run log |

## Failure Handling
- Draft fails: retry once with simpler prompt, log failure if still fails
- Post fails: log to content.md with error, do NOT retry (avoid duplicate posts)
- CAPTCHA: emit PendingAction, halt this run, alert operator via Slack

## Done Condition
Run is complete when `vault/runs/YYYY-MM-DD/content.md` is written with status
for each scheduled post, regardless of success/failure on individual posts.
