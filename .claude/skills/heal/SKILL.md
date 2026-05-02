---
name: heal
description: Trigger the self-healing state machine on demand.
---

## Use this to manually run incident detection / fix

The heartbeat normally polls every 5 min. To run on-demand:

```bash
python -m agent_os.orchestrator.heartbeat --once
```

The state machine reads `vault/genome/incidents.yaml`, classifies the failure, applies a known genome fix or spawns a 3-agent diagnostic council.
