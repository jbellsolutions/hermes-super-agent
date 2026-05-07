"""NATS JetStream subscriber — Admiral's fleet-wide event listener.

Subscribes to the wildcard subject ``agents.>`` so every agent's heartbeat,
task update, and alert arrives in real time without polling.

JetStream durable consumer ensures missed events (e.g., Admiral restart)
are replayed from the last acknowledged position.

Usage:
    from agent_os.bus.nats_subscriber import Subscriber

    sub = Subscriber(agent_id="admiral")
    await sub.start(handler=my_handler)  # runs until cancelled
    # or:
    async with Subscriber(agent_id="admiral") as sub:
        async for event in sub.events():
            handle(event)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Awaitable

logger = logging.getLogger(__name__)

_NATS_URL = os.getenv("NATS_URL", "")
_STREAM_NAME = "FLEET"
_FLEET_SUBJECT = "agents.>"  # wildcard — all agent events


@dataclass
class FleetEvent:
    subject: str
    agent_id: str
    event_type: str      # heartbeat | task.started | task.completed | alert | ...
    payload: dict[str, Any]
    raw_subject: str = field(repr=False, default="")

    @classmethod
    def from_msg(cls, msg: Any) -> "FleetEvent":
        subject = msg.subject
        parts = subject.split(".")  # agents.{id}.{type...}
        agent_id = parts[1] if len(parts) > 1 else "unknown"
        event_type = ".".join(parts[2:]) if len(parts) > 2 else "unknown"
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            payload = {"raw": msg.data.decode(errors="replace")}
        return cls(
            subject=subject,
            agent_id=agent_id,
            event_type=event_type,
            payload=payload,
            raw_subject=subject,
        )


EventHandler = Callable[[FleetEvent], Awaitable[None]]


class Subscriber:
    """Fleet-wide NATS subscriber for Admiral Hermes.

    Creates a JetStream durable consumer so events are not lost on restart.
    Falls back to a core-NATS subscribe if JetStream is unavailable.
    """

    def __init__(self, agent_id: str = "admiral", url: str | None = None) -> None:
        self._agent_id = agent_id
        self._url = url or _NATS_URL
        self._nc: Any = None
        self._js: Any = None
        self._sub: Any = None

    async def __aenter__(self) -> "Subscriber":
        await self._connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    async def _connect(self) -> None:
        if not self._url:
            logger.warning("NATS_URL not set — Subscriber is a no-op")
            return
        try:
            import nats  # type: ignore[import]
            self._nc = await nats.connect(self._url)
            self._js = self._nc.jetstream()
            await self._ensure_stream()
            logger.info("NATS Subscriber connected: %s → %s", self._url, _FLEET_SUBJECT)
        except Exception as exc:
            logger.warning("NATS Subscriber connect failed (%s)", exc)

    async def _ensure_stream(self) -> None:
        """Create the FLEET stream if it doesn't exist yet."""
        try:
            import nats.js.api as jsapi  # type: ignore[import]
            await self._js.add_stream(
                name=_STREAM_NAME,
                subjects=[_FLEET_SUBJECT, "fleet.commands.>"],
                retention=jsapi.RetentionPolicy.LIMITS,
                max_msgs=1_000_000,
                max_age=86_400 * 7,  # 7 days
            )
        except Exception:
            pass  # stream already exists — that's fine

    async def start(self, handler: EventHandler) -> None:
        """Run until cancelled, calling handler for each FleetEvent."""
        if not self._nc:
            logger.warning("NATS not available — Subscriber.start() is a no-op")
            return

        consumer_name = f"{self._agent_id}-fleet-consumer"
        try:
            self._sub = await self._js.subscribe(
                _FLEET_SUBJECT,
                durable=consumer_name,
                deliver_policy="new",
            )
        except Exception:
            # Fallback: core NATS subscribe (no persistence)
            self._sub = await self._nc.subscribe(_FLEET_SUBJECT)

        logger.info("Fleet subscriber active — listening on agents.>")
        async for msg in self._sub.messages:
            try:
                event = FleetEvent.from_msg(msg)
                await handler(event)
                if hasattr(msg, "ack"):
                    await msg.ack()
            except Exception as exc:
                logger.exception("Handler error for %s: %s", msg.subject, exc)

    async def events(self) -> AsyncIterator[FleetEvent]:
        """Async generator — yields FleetEvents one at a time."""
        if not self._nc:
            return

        consumer_name = f"{self._agent_id}-fleet-gen-consumer"
        try:
            sub = await self._js.subscribe(
                _FLEET_SUBJECT,
                durable=consumer_name,
                deliver_policy="new",
            )
        except Exception:
            sub = await self._nc.subscribe(_FLEET_SUBJECT)

        async for msg in sub.messages:
            event = FleetEvent.from_msg(msg)
            if hasattr(msg, "ack"):
                await msg.ack()
            yield event

    async def stop(self) -> None:
        if self._sub:
            try:
                await self._sub.unsubscribe()
            except Exception:
                pass
        if self._nc:
            try:
                await self._nc.drain()
            except Exception:
                pass


# ------------------------------------------------------------------
# Default fleet event logger (used by Admiral at startup)
# ------------------------------------------------------------------

async def default_fleet_handler(event: FleetEvent) -> None:
    """Log all fleet events. Admiral wires richer handlers on top."""
    if event.event_type == "heartbeat":
        logger.debug("💓 %s heartbeat: %s", event.agent_id, event.payload.get("status", "ok"))
    elif event.event_type.startswith("task."):
        task_id = event.payload.get("task_id", "?")
        logger.info("📋 %s %s task=%s", event.agent_id, event.event_type, task_id)
    elif event.event_type == "alert":
        kind = event.payload.get("kind", "unknown")
        logger.warning("🚨 %s alert [%s]: %s", event.agent_id, kind, event.payload)
    else:
        logger.debug("🌐 %s %s: %s", event.agent_id, event.event_type, event.payload)
