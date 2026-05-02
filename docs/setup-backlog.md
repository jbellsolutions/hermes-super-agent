# Super Agent Setup Backlog

This is the working backlog for tools, skills, runtimes, and integrations that still need setup.

## Current stable baseline

Verified working locally:

- Hermes gateway on Telegram.
- Hermes main model via OpenAI Codex provider.
- OpenRouter key configured for secondary/provider use.
- Codex CLI installed and authenticated.
- Agent Zero running locally at `http://127.0.0.1:5080`.
- A0 connector running with Read/Write and code execution enabled.
- Docker/Colima running.
- Super Agent repo tests passing.
- Safe daily update automation configured.

## Priority 0 — keep stable

- Keep disk free space healthy; this Mac is space-constrained.
- Keep Agent Zero bound to localhost unless explicitly changed.
- Never commit secrets or auth files.
- Prefer PR-based updates over direct auto-pushes to `main`.

## Priority 1 — setup gaps

### Hermes config migration

Run config migration after Hermes updates when convenient:

```bash
hermes config migrate
```

Reason: `hermes doctor` reports config version `v22 -> v23`.

### Browser/web search providers

Hermes `web` is enabled but provider keys are missing. Configure at least one search/scraping backend:

- Exa: `EXA_API_KEY`
- Tavily: `TAVILY_API_KEY`
- Firecrawl: `FIRECRAWL_API_KEY` and/or `FIRECRAWL_API_URL`
- Parallel: `PARALLEL_API_KEY`

Recommended first: Exa for high-quality research search.

### Browser automation

Hermes reports browser/browser-cdp system dependency not met even though `agent-browser` exists.

Next step:

```bash
hermes doctor --fix
hermes setup tools
```

Then verify browser automation in a fresh session.

### GitHub token for higher rate limits

`hermes doctor` reports no `GITHUB_TOKEN`, which means lower GitHub API rate limits.

Add a scoped token to `~/.hermes/.env` when needed. Do not store it in this repo.

## Priority 2 — high-value integrations

### Peter/steipete tool intake

Prioritized intake is documented in `docs/steipete-tool-intake.md`.

Add first, one at a time with smoke tests:

- Peekaboo for macOS screenshots/visual awareness.
- macos-automator-mcp for AppleScript/JXA app automation.
- gogcli for Google Workspace CLI workflows.
- wacli for WhatsApp CLI workflows.
- claude-code-mcp for Claude Code as an MCP specialist.
- agent-rules as curated standards/skill seed material.
- mcporter for MCP packaging/ergonomics.

Do not bulk-install the whole list. Each tool needs install docs, permission notes, and a health check.

### Optional cloud computer / Orgo AI

Decision doc: `docs/cloud-computer-options.md`.

Current recommendation: do not make Orgo AI a default dependency. Add it conditionally for VPS/customer deployments that need an isolated visible desktop, persistent browser GUI, or premium demo workspace.

Before implementation, collect Orgo API/auth docs, cost model, teardown controls, and security boundaries. Then add as an optional runtime under `src/agent_os/runtimes/orgo/`.

### Linear

Useful for project/task tracking if Justin wants agent-managed issues.

Skill exists: `linear`.

Needs Linear API token.

### Notion or Google Workspace

Useful for docs, drive, calendar, and business ops.

Skills exist:

- `notion`
- `google-workspace`

Needs provider auth setup.

### Slack or Discord gateway

Useful if Super Agent should live beyond Telegram.

Hermes currently has Telegram configured; Slack/Discord are not configured.

### Email

Useful for inbox triage, outbound drafts, and business workflows.

Skill exists: `himalaya`.

Needs IMAP/SMTP auth setup.

## Priority 3 — specialized/optional

### Voice stack

Hermes TTS is available; full voice-to-voice can be improved with STT/TTS provider setup.

Options:

- local faster-whisper
- Groq Whisper
- OpenAI Whisper
- ElevenLabs/OpenAI/MiniMax TTS

### Home Assistant / Hue / Spotify

Only configure if Justin wants smart-home/media control.

### RL / evaluation / W&B

Only configure when actively doing model training/evals.

Requires keys such as `TINKER_API_KEY` and `WANDB_API_KEY`.

### Agent OS vendored runtimes

Agent OS has runtime manifests for OpenClaw, browser-use, Aider, E2B, Exa, LiveKit, etc. Some need submodule initialization, API keys, or runtime-specific setup before they are fully operational.

## Documentation rule

Whenever a tool is added or configured:

1. Update this file.
2. Update `docs/super-agent-runtime.md` if it affects runtime behavior.
3. Update runbooks/setup docs with commands.
4. Add tests or health checks when possible.
5. Commit and push the change.
