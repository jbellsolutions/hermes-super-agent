# Commercial Packaging

Super Agent is built like a commercial product even when used internally. The repo must be safe to hand to Claude Code, Codex, another Hermes agent, or a human operator and have it walk through setup in natural language.

## Product tiers

### Operator

The default tier. This is the always-on operating agent for an individual founder/operator or one internal business.

Includes:

- Hermes orchestrator.
- Codex CLI coding/runtime support.
- Core terminal/file/browser tools.
- MCP/API tooling.
- Telegram or Slack gateway.
- Vault memory and project registry.
- Safe daily update posture.
- Business onboarding interview.

Use when:

- The customer wants one durable assistant/COO.
- The workflows are mostly code, docs, APIs, SaaS tools, browser automation, and dashboards.
- Cost and stability matter more than a flashy visible computer.

### Pro Operator

Operator plus the visual/local autonomous workspace.

Includes everything in Operator, plus:

- Agent Zero.
- A0 Connector host bridge.
- Optional local Mac visual tools.
- Default recommended Tier 1 tool pack, installed only when prerequisites and permissions are satisfied:
  - Peekaboo.
  - macos-automator-mcp.
  - gogcli.
  - wacli.
  - claude-code-mcp.
  - agent-rules.
  - mcporter.

Use when:

- The operator wants to watch/steer an agent visually.
- The agent needs host-computer access through A0.
- The deployment is local Mac-first or a trusted operator workstation.
- The sales/demo value of a visible agent workspace matters.

Important: Tier 1 tools are default candidates for Pro Operator, not mandatory global dependencies. The installer should ask natural-language questions, install only relevant tools, and skip anything that fails a prerequisite or permission check.

### Enterprise

Multi-tenant, customer-isolated, sellable deployment.

Includes everything in Pro Operator where appropriate, plus:

- Per-customer/project isolation.
- Railway/DigitalOcean/VPS deployment path.
- Central control plane / Paperclip-style dashboard.
- Agent company hierarchy templates.
- Cost caps and customer-level budgets.
- Approval gates for risky actions.
- Optional Orgo AI or equivalent managed cloud computer per customer/workspace.
- Audit logs and rollback records.

Use when:

- Multiple businesses/projects/customers run at once.
- Customer data must be isolated.
- Agents need to run persistently on Railway, DigitalOcean, or a VPS.
- A visible managed cloud computer is worth the additional cost.

## Orgo AI positioning

Orgo is not a baseline install and should not block setup.

Orgo becomes valuable in Enterprise when:

- A headless VPS needs a persistent visible desktop/browser.
- Customer isolation requires one machine per customer/workspace.
- A human needs to watch/take over the agent's cloud computer.
- The customer pays for the premium workspace.

If none of those are true, use Hermes/Codex/browser-use/Agent Zero first.

## Natural-language setup contract

Every launch path must behave like a guided onboarding consultant, not a script dump.

The installer or agent should ask:

1. Who is the operator/customer?
2. What business or project is this for?
3. Is this internal use or client/customer deployment?
4. Which tier: Operator, Pro Operator, or Enterprise?
5. Which channels are needed first: Telegram, Slack, web, voice?
6. Where should it run: local, Railway, DigitalOcean/VPS, Docker Compose, Fly?
7. Which API keys are already available?
8. Which integrations are required now vs later?
9. What are the first three workflows the agent should own?
10. What actions require human approval?

After setup it should produce:

- A summary of what is live.
- A summary of what was skipped and why.
- The exact next step.
- A project registry entry.
- A setup log/update in this repo.

## Tool install policy

- Operator installs only core dependencies.
- Pro Operator offers Tier 1 tool pack setup, one tool at a time with smoke tests.
- Enterprise offers cloud/VPS/customer-isolation options.
- Optional tools must never be hard dependencies unless their tier explicitly requires them.
- Every new tool needs docs, runbook, smoke test, and setup-instruction update.

## Sellable default

The default experience should feel like:

> "Drop the repo link into Claude Code or Codex. It interviews you about your business, asks for only the keys needed for your chosen tier, installs what is safe, verifies everything, and gives you an always-on operator plus the path to add specialist agents later."

That is the product promise.
