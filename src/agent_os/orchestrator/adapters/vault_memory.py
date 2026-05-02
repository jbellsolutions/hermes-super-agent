"""Adapter that wires Hermes' memory to the markdown Vault.

Hermes natively persists memory to its own backend. We override that with the
Vault adapter so every channel (Slack, Telegram, web, voice) reads from / writes
to the same source of truth.
"""
from __future__ import annotations

import os
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()


def conversation_path(canonical_user_id: str) -> Path:
    return VAULT_ROOT / "conversations" / f"{canonical_user_id}.md"


def append_message(canonical_user_id: str, role: str, content: str) -> None:
    """TODO(stage-2): append-only message log used by every channel."""
    p = conversation_path(canonical_user_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(f"\n## {role}\n\n{content}\n")


def load_history(canonical_user_id: str) -> str:
    p = conversation_path(canonical_user_id)
    return p.read_text() if p.exists() else ""
