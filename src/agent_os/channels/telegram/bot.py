"""Telegram bot — long-polling listener for the Admiral.

Lightweight: uses httpx (already in deps) to call Telegram's getUpdates API.
No python-telegram-bot dependency. ~150 lines.

What it does:
  1. Long-polls Telegram for new messages (every 30s timeout).
  2. For each inbound message: classify tier → plan → run dispatch → reply.
  3. For Tier 2/3 jobs: shows the plan card and waits for "yes"/"no" reply.
  4. Posts task results back to the user.

Auth model: TELEGRAM_BOT_TOKEN env var. The bot only responds to chat IDs in
TELEGRAM_CHAT_ID (comma-separated). Other chats are ignored — never auto-respond
to strangers.

Run:
    from agent_os.channels.telegram.bot import run_bot
    asyncio.create_task(run_bot())
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"
_PENDING_APPROVALS: dict[int, dict[str, Any]] = {}  # chat_id → {job, plan, decision}


def _bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def _allowed_chats() -> set[str]:
    raw = os.getenv("TELEGRAM_CHAT_ID", "")
    return {c.strip() for c in raw.split(",") if c.strip()}


async def _send(client: httpx.AsyncClient, chat_id: int, text: str) -> None:
    """Send a message to a chat. Best-effort; logs failures, never raises."""
    if not _bot_token():
        return
    try:
        await client.post(
            f"{_API_BASE}/bot{_bot_token()}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as exc:
        logger.warning("Telegram sendMessage failed: %s", exc)


async def _handle_message(client: httpx.AsyncClient, msg: dict[str, Any]) -> None:
    """Process one inbound Telegram message."""
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text:
        return

    # Allowlist check — ignore unknown chats
    allowed = _allowed_chats()
    if allowed and str(chat_id) not in allowed:
        logger.info("Ignoring message from unallowed chat_id=%s", chat_id)
        return

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
        # Save pending; ask for explicit YES.
        _PENDING_APPROVALS[chat_id] = {"job": job, "plan": tool_plan}
        await _send(
            client, chat_id,
            f"{card}\n\n*Tier {decision.tier}* — reply *yes* to run, anything else cancels.",
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

    # Format the result compactly
    if isinstance(result, dict):
        status = result.get("status", "?")
        note = result.get("note", "")
        body = "\n".join(f"`{k}`: {v}" for k, v in result.items() if k not in ("artifacts",))[:1200]
        await _send(client, chat_id, f"✓ *{status}*\n{body}")
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
                    logger.warning("Telegram getUpdates returned error: %s", data)
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
