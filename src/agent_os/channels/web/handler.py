"""Web channel handler — feeds messages into Hermes via the same vault_memory adapter."""
from __future__ import annotations

from agent_os.channels._identity import canonical
from agent_os.orchestrator.adapters.vault_memory import append_message


def on_message(session_id: str, text: str) -> str:
    """TODO(stage-8): stream Hermes' reply tokens back through WS; for now stub."""
    user_id = canonical("web", session_id)
    append_message(user_id, "user[web]", text)
    return f"(stub reply for: {text[:80]})"
