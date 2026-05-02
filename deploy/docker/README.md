# Docker Compose deploy

```bash
docker compose -f deploy/docker/compose.yml up
```

Stands up: orchestrator + upgrader (24h cron) + webapp + dashboard + Langfuse + Postgres.
