"""Walk all manifest.yaml files in the workspace and build the system graph."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from agent_os.manifest.schema import validate

ROOT = Path(os.environ.get("AGENT_OS_ROOT", ".")).resolve()
GRAPH_OUT = ROOT / "vault" / "graph" / "system.yaml"


def build_graph() -> dict[str, Any]:
    """Find every manifest.yaml in the repo, validate, build a graph dict."""
    nodes: list[dict] = []
    edges: list[dict] = []
    for path in ROOT.rglob("manifest.yaml"):
        if "/.git/" in str(path) or "/vendor/" in str(path) or "/node_modules/" in str(path):
            continue
        try:
            data = yaml.safe_load(path.read_text())
            m = validate(data)
        except Exception as e:
            print(f"skip {path}: {e}")
            continue
        nodes.append({"id": m.component, "type": m.type, "path": str(path.relative_to(ROOT))})
        for dep, version in m.depends_on.items():
            edges.append(
                {"from": m.component, "to": dep, "rel": "depends_on", "version": version}
            )
        for out in m.outputs:
            edges.append(
                {"from": m.component, "to": out.consumer, "rel": "produces", "type": out.type}
            )
        for src in m.data_sources:
            edges.append({"from": m.component, "to": src, "rel": "consumes"})
    graph = {"nodes": nodes, "edges": edges}
    GRAPH_OUT.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_OUT.write_text(yaml.safe_dump(graph, sort_keys=False))
    return graph


if __name__ == "__main__":
    import json
    g = build_graph()
    print(json.dumps({"nodes": len(g["nodes"]), "edges": len(g["edges"])}, indent=2))
