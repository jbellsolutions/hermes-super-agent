"""Resolve channel-specific user IDs to a canonical identity.

Without this, Slack-Justin and Telegram-Justin and web-Justin look like
different users to Hermes' memory. With this, they're all the same person.
"""
from __future__ import annotations

import os

# TODO(stage-7): replace with a real lookup table or auth provider.
DEFAULT_OWNER = os.environ.get("AGENT_OS_OWNER", "justin")


def canonical(channel: str, channel_user_id: str) -> str:
    return DEFAULT_OWNER
