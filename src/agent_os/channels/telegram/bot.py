"""Telegram bot — long-polling listener for the Admiral.

Lightweight: uses httpx (already in deps) to call Telegram's getUpdates API.
No python-telegram-bot dependency. ~250 lines.

What it does:
  1. Long-polls Telegram for new messages.
  2. For each inbound message: classify tier → plan → run dispatch → reply.
  3. For Tier 2/3 jobs: shows the plan card and waits for "yes"/"no" reply.
  4. Posts task results back to the user.
  5. Subscribes to NATS agents.>.alert and forwards alerts to Telegram.

Auth model: TELEGRAM_BOT_TOKEN env var. The bot only responds to chat IDs in
TELEGRAM_CHAT_ID (comma-separated). Other chats are ignored — never auto-respond
to strangers.

Run:
    from agent_os.channels.telegram.bot import run_bot, run_alert_forwarder
    asyncio.create_task(run_bot())
    asyncio.create_task(run_alert_forwarder())
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"

# chat_id → {job, plan, expires_at}.
# Approvals expire after 5 min so they don't accumulate forever.
_PENDING_APPROVALS: dict[int, dict[str, Any]] = {}
_APPROVAL_TTL_SECONDS = 300

# Telegram message hard cap is 4096 chars; leave headroom for our wrapper text.
_MAX_BODY_CHARS = 3500


def _gc_approvals() -> None:
    now = time.time()
    expired = [cid for cid, p in _PENDING_APPROVALS.items() if p.get("expires_at", 0) < now]
    for cid in expired:
        _PENDING_APPROVALS.pop(cid, None)


def _bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def _allowed_chats() -> set[str]:
    raw = os.getenv("TELEGRAM_CHAT_ID", "")
    return {c.strip() for c in raw.split(",") if c.strip()}


async def _send(client: httpx.AsyncClient, chat_id: int, text: str) -> None:
    """Send a message to a chat. Best-effort; never raises.

    Uses plain text (no parse_mode) so Markdown-special chars in user prompts
    or task results don't cause Telegram to reject the message. If we ever
    want bold/code, switch to MarkdownV2 with full escaping per Telegram docs.

    Honors 429 rate limits via the retry_after field.
    """
    if not _bot_token():
        return
    if len(text) > _MAX_BODY_CHARS:
        text = text[:_MAX_BODY_CHARS] + "\n…(truncated)"
    for attempt in range(3):
        try:
            r = await client.post(
                f"{_API_BASE}/bot{_bot_token()}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            if r.status_code == 429:
                retry_after = (r.json().get("parameters") or {}).get("retry_after", 5)
                await asyncio.sleep(min(int(retry_after), 30))
                continue
            return
        except Exception as exc:
            logger.warning("Telegram sendMessage attempt %d failed: %s", attempt + 1, exc)
            await asyncio.sleep(2)


async def _handle_message(client: httpx.AsyncClient, msg: dict[str, Any]) -> None:
    """Process one inbound Telegram message."""
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return

    # Allowlist check — fail closed if no allowlist is configured.
    # An open bot is a remote-execution endpoint for whoever finds the username.
    allowed = _allowed_chats()
    if not allowed:
        logger.warning("TELEGRAM_CHAT_ID is empty — refusing to handle messages "
                       "(set it to your chat ID to enable)")
        return
    if str(chat_id) not in allowed:
        logger.info("Ignoring message from unallowed chat_id=%s", chat_id)
        return

    # GC expired pending approvals before checking
    _gc_approvals()

    # Tier 2/3 approval reply ("yes" / "no" / "cancel")
    if chat_id in _PENDING_APPROVALS:
        decision = text.lower()
        pending = _PENDING_APPROVALS.pop(chat_id)
        if decision in ("yes", "y", "go", "approve"):
            await _dispatch_and_reply(client, chat_id, pending["job"])
        else:
            await _send(client, chat_id, "Cancelled.")
        return

    # Built-in commands
    if text.startswith("/"):
        await _send(client, chat_id, _handle_command(text))
        return

    # Lazy imports keep cold-start cheap and avoid hard deps when running
    # other parts of the system.
    from agent_os.orchestrator import plan_card, tier_classifier
    from agent_os.orchestrator.adapters.job_router import Job
    from agent_os.orchestrator.tool_planner import plan as plan_fn

    job = Job(prompt=text, tags=set())

    decision = tier_classifier.classify(job)
    tool_plan = plan_fn(job, identity="primary_hermes")
    card = plan_card.render(tool_plan, channel="markdown")

    if decision.tier >= 2:
        # Save pending with a 5-minute TTL.
        _PENDING_APPROVALS[chat_id] = {
            "job": job,
            "plan": tool_plan,
            "expires_at": time.time() + _APPROVAL_TTL_SECONDS,
        }
        await _send(
            client, chat_id,
            f"{card}\n\nTier {decision.tier} — reply 'yes' to run, anything else cancels. "
            "(Approval expires in 5 min.)",
        )
        return

    # Tier 1 — autopilot
    await _send(client, chat_id, card)
    await _dispatch_and_reply(client, chat_id, job)


async def _dispatch_and_reply(client: httpx.AsyncClient, chat_id: int, job) -> None:
    """Run the full dispatch pipeline and reply with the result."""
    from agent_os.orchestrator.adapters.job_router import dispatch
    try:
        result = await dispatch(job)
    except Exception as exc:
        logger.exception("Dispatch failed")
        await _send(client, chat_id, f"⚠️ Error: {exc}")
        return

    # Format the result compactly (plain text — no Markdown).
    if isinstance(result, dict):
        status = result.get("status", "?")
        body_lines = []
        for k, v in result.items():
            if k == "artifacts":
                continue
            v_str = str(v)
            if len(v_str) > 400:
                v_str = v_str[:400] + "…"
            body_lines.append(f"{k}: {v_str}")
        body = "\n".join(body_lines)
        await _send(client, chat_id, f"✓ {status}\n{body}")
    else:
        await _send(client, chat_id, f"✓ {result}")


def _handle_command(text: str) -> str:
    cmd = text.split()[0].lower()
    if cmd in ("/start", "/help"):
        return (
            "Hermes Admiral — your fleet brain.\n\n"
            "Just type what you want. I'll classify the tier, show you a plan, "
            "and run it (or ask for confirmation on Tier 2/3).\n\n"
            "Commands:\n"
            "  /status — quick fleet status\n"
            "  /help — this message"
        )
    if cmd == "/status":
        return "Admiral online. (Detailed fleet status TBD — wire NATS subscriber.)"
    return f"Unknown command: {cmd}"


async def run_bot() -> None:
    """Main long-polling loop. Idempotent — safe to spawn as a background task."""
    if not _bot_token():
        logger.info("TELEGRAM_BOT_TOKEN not set — Telegram bot disabled")
        return

    logger.info("Telegram bot starting (long-poll mode)")
    offset = 0

    async with httpx.AsyncClient(timeout=35) as client:
        while True:
            try:
                resp = await client.get(
                    f"{_API_BASE}/bot{_bot_token()}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                )
                data = resp.json()
                if not data.get("ok"):
                    err_code = data.get("error_code")
                    # 409 Conflict = another replica is also long-polling.
                    # Back off significantly so we don't drown the logs.
                    if err_code == 409:
                        logger.warning("Telegram 409: another instance is polling. "
                                       "Backing off 60s. Disable Railway autoscale "
                                       "or set replicas=1 for the Admiral.")
                        await asyncio.sleep(60)
                        continue
                    logger.warning("Telegram getUpdates error: %s", data)
                    await asyncio.sleep(5)
                    continue

                for update in data.get("result", []):
                    offset = max(offset, update["update_id"] + 1)
                    msg = update.get("message") or update.get("edited_message")
                    if msg:
                        # Handle each message in its own task so a slow LLM
                        # call doesn't block the poll loop.
                        asyncio.create_task(_handle_message(client, msg))
            except (httpx.HTTPError, asyncio.TimeoutError) as exc:
                logger.warning("Telegram poll error: %s — retrying in 5s", exc)
                await asyncio.sleep(5)
            except Exception:
                logger.exception("Unexpected error in Telegram poll loop")
                await asyncio.sleep(10)


# ---------------------------------------------------------------------------
# NATS → Telegram alert forwarder
# ---------------------------------------------------------------------------

async def run_alert_forwarder() -> None:
    """Forward fleet alerts (agents.>.alert) and important task events to Telegram.

    No-op if NATS_URL is unset, the nats-py library is missing, or no chat IDs
    are allowlisted. Idempotent — safe to spawn as a background task.
    """
    if not _bot_token() or not _allowed_chats():
        logger.info("Alert forwarder disabled (no Telegram bot or chat allowlist)")
        return
    if not os.getenv("NATS_URL"):
        logger.info("Alert forwarder disabled (NATS_URL not set)")
        return

    try:
        from agent_os.bus.nats_subscriber import FleetEvent, Subscriber
    except ImportError as exc:
        logger.warning("Alert forwarder disabled — bus.nats_subscriber unavailable: %s", exc)
        return

    chats = list(_allowed_chats())

    async with httpx.AsyncClient(timeout=15) as send_client:

        async def _on_event(event: FleetEvent) -> None:
            # Only forward events humans care about.
            if not _should_alert(event):
                return
            text = _format_event(event)
            for cid in chats:
                try:
                    await _send(send_client, int(cid), text)
                except ValueError:
                    logger.debug("Skipping non-numeric chat id: %s", cid)

        try:
            sub = Subscriber(agent_id="admiral-telegram-alerts")
            await sub.start(handler=_on_event)
        except Exception:
            logger.exception("Alert forwarder crashed")


def _should_alert(event) -> bool:
    """Decide whether this fleet event deserves a Telegram ping.

    Default: forward .alert events and task.failed; skip heartbeats and
    routine progress to avoid notification spam.
    """
    et = (event.event_type or "").lower()
    if et.startswith("alert"):
        return True
    if "needs_human" in (event.payload or {}):
        return True
    if et.endswith("task.failed"):
        return True
    return False


def _format_event(event) -> str:
    """One-line summary of a fleet event for Telegram delivery."""
    et = event.event_type or "event"
    aid = event.agent_id or "unknown"
    payload = event.payload or {}
    bits = []
    for key in ("error", "reason", "task_id", "needs_human", "cost_usd"):
        if key in payload:
            bits.append(f"{key}={payload[key]}")
    suffix = (" — " + ", ".join(str(b) for b in bits)) if bits else ""
    return f"⚠ [{aid}] {et}{suffix}"
