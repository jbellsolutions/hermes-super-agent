# Hermes-First Install Walkthrough

_Last updated: 2026-05-02_

## Purpose

This repo should be usable as a dropped link for a new operator, family member, customer, Claude Code session, Codex session, or terminal agent.

The intended product experience is:

```text
1. Install Hermes Agent.
2. Configure a safe default profile.
3. Connect at least one model/provider.
4. Connect one chat channel, usually Telegram.
5. Connect the shared Obsidian + Notion brain.
6. Install only the tools needed for the selected tier.
7. Verify with smoke tests before declaring ready.
```

This is the recommended first-run path for Zions' computer and for future commercial installs.

## Important status

The Super Agent repo is currently a distribution/runbook/wrapper around Hermes, Agent OS, Codex, Agent Zero/A0, Paperclip, and related tooling. A fresh machine should install Hermes Agent first, then use this repo to configure the Super Agent stack.

The repo should not assume Hermes already exists. The setup agent should check and install Hermes when missing.

## Drop-link prompt

Use this prompt in Claude Code, Codex, or another capable local coding agent on the target computer:

> Set up a Hermes Super Agent from this repo: https://github.com/jbellsolutions/hermes-super-agent. Start by checking whether Hermes Agent is installed. If Hermes is missing, install it from the official installer. Then interview me in plain English, choose the right tier, configure only the tools I need, connect the shared Obsidian/Notion brain if credentials are available, and verify everything before saying it is ready. Do not print secrets.

## Step 0 — safety and scope

Before installing anything, ask:

1. Who is this agent for?
2. Is this a personal/internal install, a project agent, a Single Brain COO install, or a customer/commercial install?
3. Which tier?
   - Operator
   - Pro Operator
   - Enterprise
4. Which computer is this?
   - local Mac
   - Windows/WSL
   - Linux/VPS
5. Which channels should work first?
   - CLI only
   - Telegram
   - Slack
   - web/API
6. What is the first job this agent should do?
7. What actions require approval?

Default approvals:

- repo edits: allowed after user confirms scope
- package installs: ask first on a personal machine
- production deploys: explicit approval required
- payment/outbound messages/customer data: explicit approval required
- destructive infra changes: explicit approval required

## Step 1 — Hermes Agent preflight

The launch wizard now does this automatically:

```bash
./scripts/launch.py
```

On startup, it checks for `hermes`. If missing, it installs Hermes from the official installer before continuing the Super Agent questions:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

If the installer updates PATH but the current terminal cannot see `hermes` yet, open a new terminal or source your shell profile, then re-run:

```bash
./scripts/launch.py
```

Manual check/install remains valid when you want to do Hermes first:

```bash
command -v hermes || true
hermes --version || true
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes --version
hermes doctor
```

## Step 2 — initial Hermes setup

Run:

```bash
hermes setup
```

At minimum configure:

- default model/provider
- terminal backend
- memory
- enabled toolsets
- gateway if Telegram/Slack is requested

Recommended model/provider posture:

- Primary architecture/debug/security profile: GPT-5.5 + Claude Opus 4.6/4.7 as dual frontier reviewers.
- Content/design/brand profile: Claude Opus 4.6/4.7.
- Mechanical worker profile: DeepSeek or another lower-cost capable model.
- Local coding backend: Codex if authenticated.
- Builder-swarm backend: Cursor SDK only when needed; use Symphony as a harness pattern/reference rather than a required dependency.

## Step 3 — clone the Super Agent repo

```bash
git clone --recurse-submodules https://github.com/jbellsolutions/hermes-super-agent.git
cd hermes-super-agent
```

If submodules fail, continue and document the failure; do not pretend the install is complete.

## Step 4 — run the Super Agent launch wizard

```bash
./scripts/launch.py
```

This command is safe on a fresh machine. The wizard starts with the Hermes preflight from Step 1: if the `hermes` CLI is missing, it installs Hermes first, verifies it can see `hermes --version`, then continues the Super Agent setup.

The wizard should collect:

- operator name
- selected tier
- business/project context
- first workflows
- approval rules
- default model/provider
- channels
- shared Obsidian/Notion sync settings
- optional deployment target
- optional tool/runtime choices

## Step 5 — shared brain setup

The Super Agent is not complete until it knows where to write and read shared operating context.

### Obsidian

Set:

```bash
OBSIDIAN_VAULT_PATH="/path/to/Obsidian Vault"
```

If unset, Hermes defaults to:

```text
~/Documents/Obsidian Vault
```

Create or verify folders:

```text
Super Agent/
Single Brain COO/
Paperclip Companies/
Projects/
People/
Vendors/
```

### Notion

Create a Notion integration and add the token to the Hermes env file, never to repo files:

```bash
hermes config env-path
```

Then add:

```text
NOTION_API_KEY=[REDACTED]
NOTION_CONVERSATIONS_DB=[database-id]
NOTION_ACTIONS_DB=[database-id]
NOTION_DECISIONS_DB=[database-id]
NOTION_AGENTS_DB=[database-id]
NOTION_COMPANIES_DB=[database-id]
NOTION_DEPLOYMENTS_DB=[database-id]
```

Share each database/page with the Notion integration.

The sync contract is bidirectional: the agent writes to Obsidian/Notion and retrieves from Obsidian/Notion before answering cross-agent or cross-business questions.

## Step 6 — choose tools by tier

### Operator

Install/configure only:

- Hermes CLI
- chosen model provider(s)
- file/terminal/git tools
- Codex if coding is needed
- one messaging channel
- Obsidian + Notion sync

### Pro Operator

Add if useful and smoke-tested:

- Agent Zero + A0 Connector
- Peekaboo
- macos-automator-mcp
- gogcli
- wacli
- claude-code-mcp
- agent-rules
- mcporter

### Enterprise

Add only when the customer/project needs it:

- VPS/Railway/DigitalOcean deployment
- isolated profiles/secrets
- approval and budget policies
- optional Orgo or managed cloud computer
- Paperclip company/team dashboard

## Step 7 — verify

Minimum verification:

```bash
hermes doctor
hermes tools list
PYTHONPATH=src uv run pytest -q
uv run agent-os manifest
```

To start the actual agent CLI, run:

```bash
hermes
```

Important: `uv run agent-os boot` is currently a Stage 2 scaffold diagnostic. If it prints JSON with `status: scaffold_not_error`, that is expected and not a failed Hermes install. Use `hermes` to start the real Hermes agent until the Super Agent boot adapter is wired.

If Telegram is enabled:

```bash
hermes gateway status
```

Then verify one full loop:

1. Send a message to the agent.
2. Ask it to summarize the setup.
3. Confirm it writes a note to Obsidian.
4. Confirm it writes/updates the expected Notion row if Notion is configured.
5. Confirm it can retrieve that context in a new session.

## Done definition

A Super Agent install is ready only when:

- Hermes runs successfully.
- A model/provider works.
- At least one interface works: CLI, Telegram, Slack, or web/API.
- Obsidian path is confirmed.
- Notion sync is either configured or explicitly marked pending.
- The selected tier's tools have been smoke-tested.
- The agent can answer: who it serves, what tools it has, what it may do without approval, and where it logs actions.

## First Zions test recommendation

For Zions' computer, start with Operator tier:

- Hermes CLI
- one model/provider
- Telegram or CLI only
- Obsidian/Notion shared sync
- no Agent Zero/A0 unless needed
- no Orgo
- no production deploy permissions

After the base loop works, upgrade to Pro Operator tools one at a time.
