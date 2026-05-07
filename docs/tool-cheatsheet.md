# Tool cheatsheet

Auto-generated from `vault/skills/active/tools/*.md`. Run `agent-os catalog`
to refresh. Authoritative source: the per-tool SKILL.md files.

| Tool | Tier | Category | Cost | Risk | Use when |
|---|---|---|---|---|---|
| `agent_zero` | 2 | visual_autonomous_workspace | medium | medium | Visual autonomous browser + host bridge. Use when the task benefits from a visible UI you can wat… |
| `aider` | 2 | coding_git_incremental | low | low | Use for git-aware incremental coding where each change is a clean commit. Aider auto-commits per… |
| `browser_use` | 2 | browser_automation | low | medium | Use for structured browser automation — scraping, QA flows, form fills, single-page interactions.… |
| `claude_managed` | 3 | long_running_cloud | high | high | Anthropic Claude Managed Agents — long-running cloud-resident jobs (>1hr). Use when the task surv… |
| `claude_subagents` | 2 | coding_interactive | medium | medium | Use for interactive coding inside this repo with Claude Code subagents — direct, in-repo, with te… |
| `codex_cli` | 2 | coding_background | medium | medium | Use for background coding via OpenAI Codex CLI — the default for GPT-5.5 coding work, multi-provi… |
| `composio` | 2 | external_connectors | low | medium | External SaaS connectors — Gmail, Slack send, GitHub, Calendar, GSheets, CRM/HubSpot, Salesforce,… |
| `computer_use` | 2 | native_desktop | medium | medium | Anthropic Computer Use SDK — raw desktop control of native (non-browser) apps. Use when the task… |
| `e2b` | 2 | sandbox_execution | low | low | E2B — clean VM per run for sandboxed code execution. Use when you want to run code that you can't… |
| `exa` | 1 | search | low | low | Exa neural search — programmatic "find me 10 articles about X" without spinning up a browser. Use… |
| `hermes_self` | 1 | orchestrator | low | low | Default. Use when the task can be answered conversationally, with a single doc or short artifact,… |
| `livekit` | 2 | voice_realtime | medium | low | LiveKit + OpenAI Realtime API or Gemini Realtime API for voice/realtime conversations. Use when t… |
| `openclaw` | 2 | autonomous_grind | medium | medium | Use when the task is autonomous shell + file + browser grind that runs for many minutes. OpenClaw… |
| `openswarm` | 2 | deliverable_production | medium | low | Use when the user asks for multi-deliverable production (slides, decks, research with charts, exe… |
| `terminal` | 1 | scripts | low | low | Plain cron-style scripts — one-shot terminal commands with no autonomous loop. Use when you know… |
