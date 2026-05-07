"""Optional NATS publisher — fire-and-forget progress events.

If NATS_URL is not set or nats-py is not installed, every call is a silent
no-op. The coordinator works fine without NATS; you just lose live progress.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_NATS_URL = os.getenv("NATS_URL", "")
_client: Any = None
_lock = asyncio.Lock()


async def _connect() -> Any:
    global _client
    if not _NATS_URL:
        return None
    if _client is not None:
        return _client
    async with _lock:
        if _client is not None:
            return _client
        try:
            import nats
            _client = await nats.connect(_NATS_URL, name="hermes-coordinator")
            logger.info("Connected to NATS at %s", _NATS_URL)
        except ImportError:
            logger.warning("nats-py not installed — NATS publishing disabled")
            _client = False  # sentinel for "tried, no library"
        except Exception as exc:
            logger.warning("NATS connect failed (%s) — disabling", exc)
            _client = False
    return _client if _client is not False else None


async def publish(subject: str, payload: dict) -> None:
    """Best-effort publish. Never raises."""
    try:
        client = await _connect()
        if not client:
            return
        await client.publish(subject, json.dumps(payload, default=str).encode())
    except Exception as exc:
        logger.debug("NATS publish to %s failed: %s", subject, exc)
