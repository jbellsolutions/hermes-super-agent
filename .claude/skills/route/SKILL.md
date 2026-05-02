---
name: route
description: Show which runtime would handle a job given its tags.
---

## Use this to verify the job router's decision

```bash
agent-os route --tags coding interactive --prompt "add a test for X"
# → claude_subagents

agent-os route --tags autonomous-grind shell --prompt "scrape and clean 1000 leads"
# → openclaw
```

Routing rules live in `packages/orchestrator/agent_os/orchestrator/adapters/job_router.py`. Default-to-Hermes is intentional — most jobs shouldn't need a specialist.
