---
name: computer_use
runtime: computer_use
tier: 2
category: native_desktop
cost_class: medium
risk_class: medium
preferred_models: [claude-opus-4.7]
mcp_or_native: native
description: Anthropic Computer Use SDK — raw desktop control of native (non-browser) apps. Use when the task is in a Mac/Linux native app (Finder, Notion native client, Photoshop, etc.) where browser automation can't reach.
---

## When to use
- Native desktop app workflows (Mac/Linux apps with no browser equivalent)
- File management via Finder/Files apps
- Tasks that cross between apps via OS-level keyboard shortcuts
- Where Anthropic's vision model on the desktop is the right fit

## When NOT to use
- Browser-only tasks → browser_use (cheaper, more reliable)
- Visual debug + host commands → agent_zero (better UX)
- Untrusted code execution → e2b
- Headless grind → openclaw or terminal

## Alternatives (ordered)
1. **agent_zero** — when you want a visible Dockerized workspace + Codex access
2. **browser_use** — if the task IS in a browser (most are)
3. **terminal** — for CLI-only desktop tasks

## Cost & latency
- Typical: $0.30–$2.00 per run (vision tokens get expensive)
- Latency: 30s–10min

## Examples
- "Open Finder, find the latest screenshot, drag it into this Notion native app"
- "Use the macOS native Photos app to apply auto-enhance to today's photos"
- "Operate this legacy desktop app that has no API"

## See also
- src/agent_os/runtimes/computer_use/manifest.yaml
- ECOSYSTEM-PLAYBOOK.md (layer 5)
