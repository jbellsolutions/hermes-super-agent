---
name: browser_use
runtime: browser_use
tier: 2
category: browser_automation
cost_class: low
risk_class: medium
preferred_models: [claude-sonnet-4.6, gpt-5.5]
mcp_or_native: native
description: Use for structured browser automation — scraping, QA flows, form fills, single-page interactions. Cheaper and lower-overhead than full computer use. Best when the page has a stable DOM and the task can be described as a sequence of element interactions.
---

## When to use
- Scraping a known site (single or paginated)
- QA flows: log in, click through, verify state, take screenshot
- Form-fill automation
- Tasks where browser-use's structured DOM extraction is enough

## When NOT to use
- Native desktop apps (no browser) → computer_use
- Visual autonomous workspace where you also need shell access → agent_zero
- Long autonomous browser grind with shell file ops mixed in → openclaw
- Pure URL fetch without interaction → exa or curl
- Anything requiring a visible cloud computer for customer demo → orgo (paid)

## Alternatives (ordered)
1. **agent_zero** — when you also need host machine access alongside the browser
2. **computer_use** — when the task crosses out of the browser
3. **openclaw** — for very long autonomous grind that mixes browser + shell

## Cost & latency
- Typical: $0.05–$0.50 per run
- Latency: 30s–5min depending on page count

## Examples
- "Scrape the pricing pages of these 20 SaaS sites, output CSV"
- "Log in to Railway, screenshot the dashboard, save it to vault/uploads"
- "Fill out this contact form on 50 site URLs"

## See also
- src/agent_os/runtimes/browser_use/manifest.yaml
- ECOSYSTEM-PLAYBOOK.md (layer 4)
