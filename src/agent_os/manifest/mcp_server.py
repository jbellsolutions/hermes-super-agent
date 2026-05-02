"""MCP server exposing the system graph as queryable resources.

TODO(stage-6): implement using the official MCP Python SDK.
Resources:
    graph://components             list with metadata
    graph://agent/{name}           agent profile + recent runs + score trend
Tools:
    trace(from, to)                walks dependency path between two components
    who_writes_to(data_source)     all agents producing into a source
    what_consumes(component)       downstream consumers
"""
from __future__ import annotations

from agent_os.manifest.aggregator import build_graph


def serve() -> None:
    raise NotImplementedError("Stage 6: implement MCP server (use modelcontextprotocol/python-sdk)")


if __name__ == "__main__":
    g = build_graph()
    print(f"loaded graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges")
