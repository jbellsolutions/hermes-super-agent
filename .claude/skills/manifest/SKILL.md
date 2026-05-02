---
name: manifest
description: Rebuild the system graph from manifest.yaml files across the workspace.
---

## Use this after adding/editing a component

```bash
agent-os manifest
# → counts nodes and edges; writes vault/graph/system.yaml
```

Every component (runtime, channel, vertical app) declares a `manifest.yaml` at its root. The aggregator walks the workspace, validates each, and builds the graph that backs `/explain` and the introspection MCP server.
