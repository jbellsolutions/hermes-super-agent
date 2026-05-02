"""Voice channel handler.

Pipeline:
    Browser audio -> WebRTC -> LiveKit room -> Voice agent worker (LiveKit Agents)
    -> OpenAI Realtime / Gemini Realtime -> text -> Hermes (with full memory)
    -> text -> Realtime synthesis -> LiveKit -> browser

Single-state guarantee: text is appended to vault/conversations/<user>.md just
like Slack/Telegram, so the same Hermes memory serves all channels.
"""
from __future__ import annotations

import os

from agent_os.channels._identity import canonical
from agent_os.orchestrator.adapters.vault_memory import append_message

PROVIDER = os.environ.get("VOICE_REALTIME_PROVIDER", "openai")  # openai | gemini


def voice_session(session_id: str, transcribed_text: str) -> str:
    """TODO(stage-9): real LiveKit Agents wiring. For now stub round-trip."""
    user_id = canonical("voice", session_id)
    append_message(user_id, f"user[voice/{PROVIDER}]", transcribed_text)
    return f"(stub voice reply for: {transcribed_text[:80]})"
