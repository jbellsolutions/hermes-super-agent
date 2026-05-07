"""AgentOps SDK initialization — single line to instrument every runtime.

AgentOps auto-instruments LLM provider SDKs (anthropic, openai, etc.) with
no further code changes once `init()` is called at process start. One
unified cost / latency / error dashboard across all 7 model backends.

Call this from each agent's entry point:

    from agent_os.observability.agentops.client import init_agentops
    init_agentops(agent_id="admiral")

Falls back to no-op if AGENTOPS_API_KEY is not set or the agentops package
is not installed. This is intentional — observability should not block boot.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_INITIALIZED = False


def init_agentops(
    agent_id: str = "admiral",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Initialize AgentOps. Returns True if instrumentation is active.

    Idempotent — safe to call multiple times across modules.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return True

    api_key = os.getenv("AGENTOPS_API_KEY", "")
    if not api_key:
        logger.debug("AGENTOPS_API_KEY not set — observability disabled")
        return False

    try:
        import agentops
    except ImportError:
        logger.warning("agentops not installed (`uv add agentops`) — observability disabled")
        return False

    try:
        agentops.init(
            api_key=api_key,
            default_tags=tags or [agent_id, "hermes-fleet"],
            instrument_llm_calls=True,
            auto_start_session=True,
        )
        _INITIALIZED = True
        logger.info("AgentOps initialized for agent_id=%s", agent_id)
        return True
    except Exception as exc:
        logger.warning("AgentOps init failed: %s", exc)
        return False


def end_session(status: str = "Success") -> None:
    """Mark the current AgentOps session done. No-op when uninitialized."""
    if not _INITIALIZED:
        return
    try:
        import agentops
        agentops.end_session(status)
    except Exception as exc:
        logger.debug("AgentOps end_session failed: %s", exc)
