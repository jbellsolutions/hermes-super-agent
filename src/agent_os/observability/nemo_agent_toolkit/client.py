"""NeMo Agent Toolkit hooks. Off by default; enable via ENABLE_NEMO_AGENT_TOOLKIT=true."""
from __future__ import annotations

import os


def enabled() -> bool:
    return os.environ.get("ENABLE_NEMO_AGENT_TOOLKIT", "false").lower() == "true"


def trace_cross_agent(coordinator: str, agent: str, action: str) -> None:
    if not enabled():
        return
    # TODO: wire NVIDIA/NeMo-Agent-Toolkit cross-agent coordination metrics
    pass
