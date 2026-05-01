# Runbook: Hermes

Hermes is the Telegram-accessible command center.

## Verify status

```bash
hermes status --all
hermes doctor
```

## Current role

Hermes coordinates:

- local shell and files
- browser automation
- Agent Zero container
- A0 connector
- Codex CLI
- documentation updates
- scheduling/cron
- memory and skills

## Gateway

```bash
hermes gateway status
hermes gateway restart
grep -i 'error\|failed' ~/.hermes/logs/gateway.log | tail -80
```

## Model preference

Justin wants Hermes main/orchestrator model kept on `gpt-5.5` via `openai-codex`.

Delegation/swarm workers can use OpenRouter models such as DeepSeek.

## Documentation habit

After a meaningful stack change:

1. Update this repo.
2. Commit changes.
3. If the workflow is reusable, create/update a Hermes skill.
