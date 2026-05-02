"""Hermes-vendored persistent orchestrator.

The orchestrator is the only always-on agent process. It owns the conversation,
the memory, the skill library, and the routing decisions. For most jobs it just
does the work itself. For specific job types it dispatches to a specialist
runtime (see agent_os.runtimes).
"""

__version__ = "0.1.0"
