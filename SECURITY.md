# Security

## Reporting a vulnerability

Email justin@usingaitoscale.com. Do not open a public issue for security-sensitive reports.

## Surface map

This repo wires together vendored OSS that runs autonomously and accesses sensitive systems. Reviewers should focus on:

1. **Vendored upstream code** (`vendor/`) — trust inherited from upstream maintainers (Nous Research, OpenClaw maintainers, browser-use, Aider-AI, NVIDIA). Auto-updater pulls nightly.
2. **Channel adapters** (`packages/channels/`) — Slack, Telegram, web app, voice. Authentication and message validation live here.
3. **Runtime adapters** (`packages/runtimes/`) — OpenClaw shell scope, browser-use allowed domains, E2B sandbox boundaries, Computer Use granted apps.
4. **Vault file permissions** — `vault/uploads/` is user-writable; do not expose externally.
5. **NemoClaw sandbox** (parked) — when enabled, OpenClaw runs inside NVIDIA OpenShell with policy-engine constraints.

## Defenses in place

- All upgrader streams smoke-test before promotion. Failed smoke quarantines on a branch with Slack alert.
- Daily token + voice-minute budgets with Slack alert at 80%.
- Vendored modules pinned to specific commits; auto-updates reviewed via the upgrader's promotion log.
- Awesome-hermes-agent community skills land as REVIEW-REQUIRED, never auto-promoted.
- All channels write through the same Vault adapter — no per-channel side-channel exfiltration.
