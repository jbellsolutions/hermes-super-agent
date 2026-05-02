# Cloud Computer Options for Super Agent

## Short answer

Cloud agents only have a "computer" if the runtime gives them one.

- A Hermes agent on a VPS has the VPS: shell, filesystem, processes, ports, Docker, and any browser/GUI stack we install.
- Codex CLI has the computer where Codex is installed and authenticated. On a VPS, that means the VPS filesystem/shell; on Justin's Mac, that means Justin's Mac.
- Hermes browser tools can use a local browser or a hosted browser backend if configured.
- Agent Zero has its Docker container and web UI; with A0 Connector it can bridge into the host computer.
- Anthropic/OpenAI computer-use style tools need an actual desktop/browser environment behind them.
- Orgo AI-style hosted machines are optional managed computers. They add isolation and demos, not magic intelligence.

## Recommendation

Do not make Orgo AI a default dependency for Super Agent yet. Make it an optional runtime for deployments where a managed cloud computer is worth the cost.

Default product posture:

1. **Local/Mac install:** Hermes + Codex + Agent Zero + A0. No Orgo needed.
2. **VPS install:** Hermes + Codex + Docker + browser tooling. Add Agent Zero if a visual UI is valuable. Add a lightweight browser stack first before paying for a managed computer.
3. **Commercial/customer install:** add Orgo or a similar managed cloud computer only when the customer needs isolated visual workspaces, browser GUI demos, fragile website automation, or per-client computer sandboxes.

## Decision rule

Use Orgo AI or a similar managed cloud computer when at least one is true:

- The Super Agent is hosted on a headless VPS but the workflow requires a persistent GUI desktop/browser that humans can watch or take over.
- Customer isolation matters and each client should get a separate cloud machine rather than sharing the agent host.
- The workflow needs long-lived browser state, logged-in SaaS sessions, or visual desktop automation that local browser-use/CDP does not handle reliably.
- The sales/demo value of a visible "agent computer" is worth the extra monthly cost.
- A customer contract can absorb the extra cost as a premium tier.

Do not use Orgo by default when:

- The job is repo coding, file editing, shell automation, data processing, or API/MCP work.
- Codex/Hermes terminal tools are enough.
- Browser-use or Hermes browser automation is enough.
- Agent Zero + A0 already provides the needed computer on a local host.
- The deployment is cost-sensitive or needs the smallest reliable footprint.

## Conditional VPS architecture

```text
Customer / Operator
        │
        ▼
Hermes Orchestrator on VPS
        │
        ├── Codex CLI on VPS for coding/repo work
        ├── Docker services for Agent Zero, databases, MCP servers
        ├── Browser-use / CDP browser for structured web tasks
        ├── Agent Zero container for visual autonomous UI, optional
        └── Orgo AI managed computer, optional premium runtime
```

## Runtime routing

- **Coding / repo changes:** Codex CLI first.
- **Long shell/file tasks:** Hermes terminal or OpenClaw runtime.
- **Structured browser tasks:** Hermes browser/browser-use first.
- **Visual desktop tasks:** Agent Zero + A0 locally; Orgo on VPS/commercial deployments if a managed machine is required.
- **High-risk customer tasks:** isolated runtime with logs, approval gates, and disposable state.

## Commercial positioning

Orgo can be a strong selling point because customers understand "your agent has its own cloud computer." That is visually compelling. The downside is cost and another moving part.

Best packaging:

- **Core tier:** Hermes + Codex + MCP/API tooling + browser automation.
- **Pro tier:** adds Agent Zero visual workspace and persistent browser/session tooling.
- **Enterprise / isolated workspace tier:** adds Orgo AI or equivalent managed cloud computers per customer/workspace.

This keeps margins healthy while preserving the sexy demo for accounts that pay for it.

## Integration backlog

Before adding Orgo as code, collect:

- Auth method and API keys.
- CLI/API install docs.
- Whether it exposes SSH, VNC/browser, MCP, REST, or SDK control.
- Cost model per machine/hour/month.
- Data retention and teardown controls.
- Network/security model for customer secrets.

Then add it as `src/agent_os/runtimes/orgo/` with:

- `invoke.py` adapter.
- Health check/smoke test.
- Manifest node.
- Runbook.
- Cost guardrails.
- Routing rule: use only when job tags include `desktop`, `visual-browser`, `isolated-computer`, or `customer-sandbox`.
