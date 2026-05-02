"""Telegram event handlers. TODO(stage-7): wire python-telegram-bot."""
from __future__ import annotations

from agent_os.channels._identity import canonical
from agent_os.orchestrator.adapters.vault_memory import append_message


def on_message(tg_update: dict) -> None:
    user_id = canonical("telegram", str(tg_update.get("from", {}).get("id", "?")))
    text = tg_update.get("text", "")
    append_message(user_id, "user[telegram]", text)
