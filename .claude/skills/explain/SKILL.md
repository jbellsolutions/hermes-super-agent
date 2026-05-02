---
name: explain
description: Walk the system graph in plain language to answer 'how do you all tie together?'.
---

## Use this to query system structure

Run `agent-os manifest` to refresh the graph, then use the manifest MCP server (`packages/manifest/agent_os/manifest/mcp_server.py`) or the helper functions in `agent_os.manifest.explain`:

- `whats_running()` — heartbeats + active runtimes + current jobs.
- `who_wrote(output_path)` — walk back from a vault output to its author agent + prompt version.
- `what_depends_on(component)` — graph walk.
- `changed_in_last_24h()` — diff manifest snapshots.

Common questions:

- *"How does cold-email-agent connect to speakeragent-api?"* → `trace(from='cold-email-agent', to='speakeragent-api')`
- *"Who consumes vault.runs?"* → `what_consumes('vault.runs')`
