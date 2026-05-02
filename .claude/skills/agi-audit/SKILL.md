---
name: agi-audit
description: Score a target (repo, vault outputs, or specific artifact) using vendor/agi-1's audit.
---

## Use this on demand or as a nightly cron

```python
from agent_os.quality import audit
result = audit("./examples/sdr-fleet")
# {"score": int, "g_stack": int, "ai_readiness": int, "findings": [...]}
```

Brain runs this nightly at 02:00 against the day's vault outputs and writes the result to `vault/daily/<date>.md`.
