"""Introspection layer — manifest schema, aggregator, MCP server, /explain backend."""
from agent_os.manifest.aggregator import build_graph
from agent_os.manifest.schema import Manifest, validate

__all__ = ["Manifest", "validate", "build_graph"]
__version__ = "0.1.0"
