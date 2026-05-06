---
name: {name}-swarm
description: {description}
runtime: openswarm
op: run
swarm: {name}
---

# {name} swarm

**When to use:** {business_purpose}

**What this produces:** {output_types}

**Example prompts that match:**
{example_block}

**Tool call:** invoke runtime `openswarm` with `op="run"`, `swarm="{name}"`, `agent="auto"` (or a specific specialist), `prompt=<user request>`, `files=<any references>`.

**Cost:** budgeted to ${cost_budget_daily_usd}/day. Hermes should warn if cumulative day cost > 80%.

**Manifest:** `{manifest_path}`
