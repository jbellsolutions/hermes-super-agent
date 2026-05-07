"""NATS JetStream publisher — emits fleet events from any agent.

Called by job_router.py on task lifecycle transitions and from the
heartbeat loop. Gracefully no-ops if NATS_URL is not set so the
system runs locally without NATS installed.

Usage:
    from agent_os.bus.nats_publisher import publish_event, Publisher

    # fire-and-forget (sync wrapper, safe to call from anywhere):
    publish_event("agents.admiral.task.started", {"task_id": "abc", "prompt": "..."})

    # async context (preferred inside async Hermes handlers):
    async with Publisher() as pub:
        await pub.task_started("admiral", task_id, payload)
        await pub.heartbeat("admiral", {"status": "green"})
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_NATS_URL = os.getenv("NATS_URL", "")  # e.g. nats://user:pass@nats.railway.internal:4222


def _nats_available() -> bool:
    return bool(_NATS_URL)


class Publisher:
    """Async context manager wrapping a NATS connection."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url or _NATS_URL
        self._nc: Any = None  # nats.aio.client.Client

    async def __aenter__(self) -> "Publisher":
        if not self._url:
            logger.debug("NATS_URL not set — publisher is a no-op")
            return self
        try:
            import nats  # type: ignore[import]
            self._nc = await nats.connect(self._url)
            logger.debug("NATS connected: %s", self._url)
        except Exception as exc:  # pragma: no cover
            logger.warning("NATS connect failed (%s) — running without bus", exc)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._nc:
            try:
                await self._nc.drain()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Low-level publish
    # ------------------------------------------------------------------

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        if not self._nc:
            return
        data = json.dumps({**payload, "_ts": time.time()}).encode()
        try:
            await self._nc.publish(subject, data)
        except Exception as exc:
            logger.warning("NATS publish failed on %s: %s", subject, exc)

    # ------------------------------------------------------------------
    # Typed event helpers  (subject = agents.{agent_id}.*)
    # ------------------------------------------------------------------

    async def heartbeat(self, agent_id: str, payload: dict[str, Any] | None = None) -> None:
        await self.publish(f"agents.{agent_id}.heartbeat", payload or {})

    async def task_started(self, agent_id: str, task_id: str, payload: dict[str, Any] | None = None) -> None:
        await self.publish(f"agents.{agent_id}.task.started", {"task_id": task_id, **(payload or {})})

    async def task_completed(self, agent_id: str, task_id: str, payload: dict[str, Any] | None = None) -> None:
        await self.publish(f"agents.{agent_id}.task.completed", {"task_id": task_id, **(payload or {})})

    async def task_failed(self, agent_id: str, task_id: str, error: str) -> None:
        await self.publish(f"agents.{agent_id}.task.failed", {"task_id": task_id, "error": error})

    async def alert(self, agent_id: str, kind: str, payload: dict[str, Any] | None = None) -> None:
        """kind: needs_human | cost_exceeded | error | degraded"""
        await self.publish(f"agents.{agent_id}.alert", {"kind": kind, **(payload or {})})

    async def fleet_command(self, agent_id: str, command: str, payload: dict[str, Any] | None = None) -> None:
        """Admiral → agent directive."""
        await self.publish(f"fleet.commands.{agent_id}", {"command": command, **(payload or {})})


# ------------------------------------------------------------------
# Sync fire-and-forget convenience (safe from sync code paths)
# ------------------------------------------------------------------

# Circuit breaker — when NATS is unreachable, don't spawn a doomed task per event.
# 3 consecutive failures opens the circuit for 60s. After cool-down we try once;
# on success it closes, on failure it stays open another 60s.
_BREAKER_FAILURE_THRESHOLD = 3
_BREAKER_OPEN_SECONDS = 60.0
_breaker_failures = 0
_breaker_open_until = 0.0


def _breaker_open() -> bool:
    return time.time() < _breaker_open_until


def _breaker_record_success() -> None:
    global _breaker_failures, _breaker_open_until
    _breaker_failures = 0
    _breaker_open_until = 0.0


def _breaker_record_failure() -> None:
    global _breaker_failures, _breaker_open_until
    _breaker_failures += 1
    if _breaker_failures >= _BREAKER_FAILURE_THRESHOLD:
        _breaker_open_until = time.time() + _BREAKER_OPEN_SECONDS
        logger.warning(
            "NATS circuit breaker opened — suppressing publish_event for %ss "
            "after %d consecutive failures.",
            _BREAKER_OPEN_SECONDS, _breaker_failures,
        )


def publish_event(subject: str, payload: dict[str, Any]) -> None:
    """Sync wrapper — creates a transient event loop if needed.

    Safe to call from synchronous code (e.g., job_router.route()). Does nothing
    if NATS_URL is not configured. Honors a process-local circuit breaker so a
    NATS outage doesn't pile up doomed tasks.
    """
    if not _nats_available():
        return
    if _breaker_open():
        return

    async def _send() -> None:
        try:
            async with Publisher() as pub:
                if pub._nc is None:
                    _breaker_record_failure()
                    return
                await pub.publish(subject, payload)
                _breaker_record_success()
        except Exception:
            _breaker_record_failure()

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send())
    except RuntimeError:
        try:
            asyncio.run(_send())
        except Exception:
            _breaker_record_failure()
