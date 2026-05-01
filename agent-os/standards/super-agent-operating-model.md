# Super Agent Operating Model

Use the right agent/tool for the job:

- **Hermes**: mission control, Telegram interface, system orchestration, files, browser, cron, memory, skills.
- **Codex**: code implementation/review inside git repos or worktrees.
- **Agent Zero**: visual/autonomous workflows, UI-observable tasks, plugin/skill experiments.
- **A0 Connector**: Agent Zero bridge to the Mac host; use for host shell/files from Agent Zero.
- **Docker/Colima**: local services, databases, sandboxes, and containers.

Rules:

- Use git repos/worktrees for code changes.
- Ask before production-impacting pushes/deploys.
- Keep secrets in auth files or `.env`, never docs/prompts.
- Update this repo when stack behavior changes.
