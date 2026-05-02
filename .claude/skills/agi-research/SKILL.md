---
name: agi-research
description: Run Karpathy autoresearch on a stalled skill — generate variations, score, promote winner.
---

## Use this when a skill plateaus or regresses

```python
from agent_os.quality import research
result = research("vault/skills/active/prospector.md", n_variations=5)
```

Promotion bar: winner > incumbent by ≥5pp on confidence-adjusted score. Old prompt archived; rollback available in dashboard.
