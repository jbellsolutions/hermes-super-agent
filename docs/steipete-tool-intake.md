# Peter Steinberger / steipete Tool Intake

Source: <https://github.com/steipete>

This page maps the open-source tools from Peter/steipete that are relevant to Super Agent. The goal is not to install everything. The goal is to add tools that make the agent more useful, intuitive, stable, and commercially valuable.

## Adoption rule

A tool gets promoted only if it passes the Super Agent filter:

1. It fills a real runtime/channel/memory/ops gap.
2. It is open source and installable reproducibly.
3. It can be wrapped as a Hermes skill, MCP server, CLI runtime, or optional package without confusing the orchestrator.
4. It has a smoke test or health check.
5. It does not duplicate an already-working default unless it is clearly better for a specific route.

## Priority tiers

### Tier 1 — add first

These are directly useful to a sellable Super Agent.

- **Peekaboo** — <https://github.com/steipete/Peekaboo>
  - macOS screenshot + optional MCP/VQA for agents.
  - Value: gives local Mac agents better visual awareness and app screenshots.
  - Integration: optional macOS runtime + MCP server; Hermes skill for screenshot/VQA workflows.
  - Notes: macOS-only; requires screen-recording permissions.

- **macos-automator-mcp** — <https://github.com/steipete/macos-automator-mcp>
  - AppleScript/JXA automation through MCP.
  - Value: local Mac app control, especially for demos and operator workflows.
  - Integration: optional MCP server in Hermes config; runbook for permissions.
  - Notes: powerful; needs approval/safety boundaries.

- **gogcli** — <https://github.com/steipete/gogcli>
  - Google Suite CLI: Gmail, Calendar, Drive, Contacts.
  - Value: strong business utility; good for COO/assistant workflows.
  - Integration: productivity runtime or Hermes skill; compare with existing `google-workspace` skill before duplicating.

- **wacli** — <https://github.com/steipete/wacli>
  - WhatsApp CLI.
  - Value: channel reach for customer/business communication.
  - Integration: optional channel tool; runbook for auth/session persistence.

- **claude-code-mcp** — <https://github.com/steipete/claude-code-mcp>
  - Claude Code as a one-shot MCP server.
  - Value: "agent in your agent" coding specialist; useful for review/alternate implementation passes.
  - Integration: MCP runtime behind routing tags `code`, `review`, `claude`.

- **agent-rules** — <https://github.com/steipete/agent-rules>
  - Rules and knowledge for better agent behavior.
  - Value: seed material for Super Agent skills/standards.
  - Integration: curate into `agent-os/standards/` and Hermes skills; do not blindly import all rules.

- **mcporter** — <https://github.com/steipete/mcporter>
  - Package/call MCPs through TypeScript APIs/CLI.
  - Value: helps standardize MCP ergonomics and packaging.
  - Integration: developer tooling, not default runtime.

### Tier 2 — useful, conditional

- **CodexBar** — <https://github.com/steipete/CodexBar>
  - Menu bar usage stats for Codex and Claude Code.
  - Value: operator visibility/cost awareness on macOS.
  - Integration: optional local operator app; not needed on VPS.

- **VibeMeter** — <https://github.com/steipete/VibeMeter>
  - AI provider cost tracking.
  - Value: commercial cost guardrails and margin protection.
  - Integration: observability/cost dashboard candidate.

- **RepoBar** — <https://github.com/steipete/RepoBar>
  - GitHub repo status in menu bar/terminal.
  - Value: local operator visibility for CI/issues/PRs/releases.
  - Integration: optional macOS operator tool; not core runtime.

- **summarize** — <https://github.com/steipete/summarize>
  - Summarize URLs, YouTube, podcasts, and files.
  - Value: convenient ingestion/summarization CLI.
  - Integration: research/content runtime; compare with existing Hermes web/youtube skills to avoid duplication.

- **slacrawl** — <https://github.com/steipete/slacrawl>
  - Slack crawl into SQLite.
  - Value: ingest customer Slack history for memory/search.
  - Integration: optional import pipeline with consent and retention rules.

- **birdclaw** — <https://github.com/steipete/birdclaw>
  - Stores tweets locally for agents.
  - Value: social/media research archive.
  - Integration: optional research memory source.

- **ghcrawl** — <https://github.com/steipete/ghcrawl>
  - Crawl GitHub issues/PRs, embeddings, clustering.
  - Value: repo intelligence for engineering teams.
  - Integration: optional GitHub research/indexing runtime.

- **discrawl** — <https://github.com/steipete/discrawl>
  - Discord crawl into SQLite.
  - Value: community/customer support ingestion.
  - Integration: optional import pipeline.

- **wacrawl** — <https://github.com/steipete/wacrawl>
  - WhatsApp archaeology with encrypted receipts.
  - Value: WhatsApp history ingestion/audit.
  - Integration: optional import pipeline; privacy-sensitive.

- **imsg** — <https://github.com/steipete/imsg>
  - Apple Messages CLI.
  - Value: local iMessage/SMS channel on macOS.
  - Integration: already represented by Hermes `imessage` skill; add to docs/runbooks if enabling iMessage.

- **remindctl** — <https://github.com/steipete/remindctl>
  - Apple Reminders CLI.
  - Value: personal productivity and follow-up tasks.
  - Integration: already represented by Hermes `apple-reminders` skill.

- **tmuxwatch** — <https://github.com/steipete/tmuxwatch>
  - TUI to watch tmux sessions.
  - Value: useful for monitoring Hermes/A0/Codex subagent sessions.
  - Integration: optional local ops helper.

- **oracle** — <https://github.com/steipete/oracle>
  - Invoke GPT-5 Pro with custom context and files.
  - Value: escalation path for hard problems.
  - Integration: optional research/review specialist if auth/cost model fits.

### Tier 3 — park unless a specific vertical needs it

- **Trimmy** — useful operator utility, not an agent runtime.
- **sonoscli**, **eightctl**, **camsnap** — useful for smart-home/media/camera verticals, not core Super Agent.
- Older Objective-C/iOS libraries and forks — mostly not relevant to Super Agent.

## User-mentioned tools checklist

- Vibe Tunnel: not found in the steipete repo list returned by GitHub API during this intake; needs exact URL/name before integration.
- Codexbar: Tier 2 optional macOS operator tool.
- Peekaboo: Tier 1.
- Summarize: Tier 2.
- Google CLI: `gogcli`, Tier 1.
- Whatsapp CLI: `wacli`, Tier 1.
- Slack History / Slack crawl: `slacrawl`, Tier 2 ingestion.
- Bird crawl: `birdclaw`, Tier 2 ingestion.
- Vox / ElevenLabs kit / BS log / GIF / G rep: names ambiguous from the GitHub API list; needs exact URLs before adopting.
- Mac OS Automator: `macos-automator-mcp`, Tier 1.
- MCP: `mcporter` and `claude-code-mcp`, Tier 1.
- Claude Code: `claude-code-mcp`, Tier 1; also keep native Claude Code runtime.
- MCP Agent Scripts: likely `claude-code-mcp`, `mcporter`, and/or `agent-rules`; verify exact target.
- Agent Rules: Tier 1.
- Homebrew Tap: if Peter publishes a general tap, use it for install ergonomics. The GitHub API list surfaced `homebrew-zld`, which is not a Super Agent priority.

## Integration backlog

1. Create `docs/steipete-tool-install-plan.md` with install commands and smoke tests for Tier 1.
2. Add optional runtime/skill docs for Peekaboo, macos-automator-mcp, gogcli, wacli, claude-code-mcp, agent-rules, and mcporter.
3. Add cost/permissions warnings for every tool touching private messages, Slack, WhatsApp, Gmail, screen capture, or local app automation.
4. Add health checks where possible:
   - `peekaboo --help` and screenshot permission check.
   - MCP server startup check for macos-automator-mcp and claude-code-mcp.
   - `gogcli --help` plus auth status.
   - `wacli --help` plus session status.
5. Promote tools one at a time. Do not batch-install all Tier 1 tools without smoke tests.

## Commercial view

The strongest commercial story from this set is:

- Visual computer awareness: Peekaboo + optional cloud computer.
- Business data access: gogcli, Slack/WhatsApp/Discord crawlers with consent.
- Communication channels: WhatsApp CLI, iMessage where macOS is available.
- Engineering leverage: claude-code-mcp, ghcrawl, agent-rules.
- Cost/ops polish: CodexBar/VibeMeter/RepoBar for the operator edition.

That makes Super Agent feel bigger without turning it into an unmaintainable pile of tools.
