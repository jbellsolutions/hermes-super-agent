"""Slack event handlers. Single-state guarantee enforced via vault_memory."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from agent_os.channels._identity import canonical
from agent_os.orchestrator.adapters.vault_memory import append_message

VAULT_UPLOADS = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve() / "uploads"


def on_message(slack_event: dict) -> None:
    """TODO(stage-7): forward to Hermes; for now log to vault."""
    user_id = canonical("slack", slack_event.get("user", "?"))
    text = slack_event.get("text", "")
    append_message(user_id, "user[slack]", text)


def on_file_upload(slack_event: dict, file_bytes: bytes, filename: str) -> str:
    """Persist uploaded file to vault, return its canonical path for Hermes context."""
    sha = hashlib.sha256(file_bytes).hexdigest()[:16]
    VAULT_UPLOADS.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix
    path = VAULT_UPLOADS / f"{sha}{ext}"
    path.write_bytes(file_bytes)
    user_id = canonical("slack", slack_event.get("user", "?"))
    append_message(user_id, "user[slack/file]", f"[uploaded: {filename}]({path})")
    return str(path)
