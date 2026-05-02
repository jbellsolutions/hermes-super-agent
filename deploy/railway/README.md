# Railway deploy

```bash
railway up
```

Provisions:
- Hermes orchestrator (always-on Python service via `uv run agent-os boot`)
- Webapp (Next.js, port 3002)
- Dashboard (Next.js, port 3001)
- Postgres for vault Supabase mirror
- Optional: LiveKit Cloud or self-hosted LiveKit
