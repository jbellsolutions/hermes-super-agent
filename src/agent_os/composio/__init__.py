"""Composio — built-in tool access for agent-os.

Three functions Hermes is told about at boot, callable from any conversation
or skill:

    composio.discover(query)     find tools matching a natural-language query
    composio.connect(app)        kick off OAuth, persist connection
    composio.call(tool, args)    invoke a tool, get a result

Authentication is via COMPOSIO_API_KEY. Per-app connections live in
vault/composio/connections.yaml — Hermes writes them on demand.
"""
from agent_os.composio.client import call, is_configured
from agent_os.composio.connect import connect, list_connections
from agent_os.composio.discover import discover

__all__ = ["call", "connect", "discover", "is_configured", "list_connections"]
__version__ = "0.1.0"
