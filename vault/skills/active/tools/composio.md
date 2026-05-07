---
name: composio
runtime: composio
tier: 2
category: external_connectors
cost_class: low
risk_class: medium
preferred_models: [claude-sonnet-4.7, gpt-5.5]
mcp_or_native: mcp
description: External SaaS connectors — Gmail, Slack send, GitHub, Calendar, GSheets, CRM/HubSpot, Salesforce, etc. Use when the task needs structured action against a SaaS API and Composio has the connector. Cheaper and more reliable than browser automation for known APIs.
---

## When to use
- Sending email via Gmail
- Posting messages or files to Slack
- Creating/updating GitHub issues or PRs
- Reading/writing Google Sheets
- Calendar reads/creates
- CRM operations (HubSpot/Salesforce)
- Any "I have a structured intent → execute against this SaaS API"

## When NOT to use
- Pages without API support → browser_use
- Sensitive infra changes (deploys, force-push) → terminal + approval gate
- Reads of vault data → hermes_self / explain
- Customer demos that need visible automation → agent_zero / orgo

## Alternatives (ordered)
1. **browser_use** — when no Composio connector or API exists
2. **terminal** — for CLI-friendly tools (gh CLI, `slack-cli`, etc.)
3. **mcp_registry** — when a more specific MCP server is registered

## Cost & latency
- Typical: $0.001–$0.05 per action (Composio is cheap)
- Latency: 1–5s per action
- Risk: medium because Composio writes to external systems — Tier 2 plan card surfaces the action before sending

## Examples
- "Send the deck PDF to client@example.com via Gmail with this body"
- "Post this announcement to #general"
- "Create a GitHub issue in jbellsolutions/repo with these labels"
- "Update HubSpot deal X to stage 'Closed Won'"

## See also
- vendor/composio (if vendored) or upstream
- ECOSYSTEM-PLAYBOOK.md (layer 13 — CRM/RevOps reach)
