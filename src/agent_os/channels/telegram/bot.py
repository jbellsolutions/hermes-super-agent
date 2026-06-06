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

# chat_id → active identity name (set via /identity <name>).
# Falls back to AGENT_IDENTITY env var when not set.
_ACTIVE_IDENTITY: dict[int, str] = {}

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

    # Lazy imports keep cold-start cheap and avoid hard deps when running
    # other parts of the system.
    from agent_os.orchestrator import intent_classifier, plan_card
    from agent_os.orchestrator.adapters import plan_overrides
    from agent_os.orchestrator.adapters.job_router import Job
    from agent_os.orchestrator.tool_planner import plan as plan_fn

    # Override commands (/cancel, /use, /why, /plan on|off, /tier N, YES) — these
    # take precedence over both pending-approval flows and free-form prompts.
    override = plan_overrides.parse(text)

    if override is not None and override.kind != "unknown":
        pending = _PENDING_APPROVALS.get(chat_id)

        if override.kind == "cancel":
            _PENDING_APPROVALS.pop(chat_id, None)
            await _send(client, chat_id, "Cancelled.")
            return

        if override.kind == "why":
            if not pending:
                await _send(client, chat_id, "No active plan to explain. "
                                              "Send a request first, then /why.")
                return
            await _send(client, chat_id, plan_card.render(pending["plan"], channel="why"))
            return

        if override.kind == "use":
            if not pending:
                await _send(client, chat_id, "No active plan to retarget. "
                                              "Send a request first, then /use <tool>.")
                return
            tool = override.tool or ""
            from agent_os.orchestrator.adapters.job_router import KNOWN_RUNTIMES
            if tool not in KNOWN_RUNTIMES:
                await _send(client, chat_id,
                            f"Unknown tool: {tool!r}. Known: "
                            f"{', '.join(sorted(KNOWN_RUNTIMES))}")
                return
            pending["plan"].primary_tool = tool
            pending["plan"].primary_reason = "user override (/use)"
            if override.model:
                pending["plan"].model_recommendation = override.model
            await _send(client, chat_id,
                        f"Switched to `{tool}`"
                        f"{' on ' + override.model if override.model else ''}. "
                        "Reply 'yes' to run.")
            return

        if override.kind == "tier":
            if not pending:
                await _send(client, chat_id, "No active plan to retier. "
                                              "Send a request first.")
                return
            pending["plan"].tier = override.tier or 2
            await _send(client, chat_id,
                        f"Forced to tier {pending['plan'].tier}. Reply 'yes' to run.")
            return

        if override.kind == "identity":
            name = override.identity
            if not name:
                # List available identities
                from pathlib import Path  # noqa: PLC0415
                identity_dir = (
                    Path(__file__).parents[3]
                    / "orchestrator/config/identities"
                )
                available = sorted(
                    p.stem for p in identity_dir.glob("*.yaml")
                )
                current = _ACTIVE_IDENTITY.get(chat_id) or os.getenv("AGENT_IDENTITY", "supersan")
                await _send(
                    client, chat_id,
                    f"Current identity: {current}\n"
                    f"Available: {', '.join(available)}\n\n"
                    "Switch with: /identity <name>",
                )
                return
            _ACTIVE_IDENTITY[chat_id] = name
            await _send(client, chat_id,
                        f"Identity set to '{name}'. All future messages will use this persona.")
            return

        if override.kind == "confirm":
            if not pending:
                await _send(client, chat_id, "No pending tier-3 plan to confirm.")
                return
            _PENDING_APPROVALS.pop(chat_id, None)
            await _dispatch_and_reply(client, chat_id, pending["job"], pending["plan"])
            return

        if override.kind in ("plan_on", "plan_off"):
            await _send(client, chat_id, f"Acknowledged: {override.kind}. "
                                          "(Per-session plan toggle TBD.)")
            return

    if override is not None and override.kind == "unknown" and override.error:
        await _send(client, chat_id, override.error)
        return

    # Tier 2 approval reply ("yes" / "no" / "cancel" — case-insensitive)
    if chat_id in _PENDING_APPROVALS:
        decision = text.lower()
        if decision in ("yes", "y", "go", "approve"):
            pending = _PENDING_APPROVALS.pop(chat_id)
            await _dispatch_and_reply(client, chat_id, pending["job"], pending["plan"])
            return
        if decision in ("no", "n", "cancel", "stop"):
            _PENDING_APPROVALS.pop(chat_id, None)
            await _send(client, chat_id, "Cancelled.")
            return
        # Anything else — drop the pending plan and treat the new message
        # as a fresh request (prevents stuck approvals on misreads).
        _PENDING_APPROVALS.pop(chat_id, None)

    # Built-in commands (legacy /start, /help, /status — handled after overrides)
    if text.startswith("/"):
        await _send(client, chat_id, _handle_command(text))
        return

    # Lane gating — empty natural-language prompts default to in-process
    # (hermes_self). intent_classifier only adds tags for spawn / fan-out /
    # outbound intent it can prove from the wording. No fuzziness, no LLM
    # call, no auto-spawn from ambiguous prompts.
    intent = intent_classifier.classify(text)
    meta: dict[str, str] = {"user_id": str(chat_id)}
    if chat_id in _ACTIVE_IDENTITY:
        meta["identity"] = _ACTIVE_IDENTITY[chat_id]
    job = Job(prompt=text, tags=set(intent.tags), metadata=meta)

    tool_plan = plan_fn(job, identity="primary_hermes")
    # tool_plan.tier already came from tier_classifier.classify with the
    # tool's cost/minutes baked in — use it directly to keep gating consistent.
    card = plan_card.render(tool_plan, channel="markdown")

    if tool_plan.tier >= 2:
        # Save pending with a 5-minute TTL.
        _PENDING_APPROVALS[chat_id] = {
            "job": job,
            "plan": tool_plan,
            "expires_at": time.time() + _APPROVAL_TTL_SECONDS,
        }
        prompt_word = "YES" if tool_plan.tier == 3 else "yes"
        await _send(
            client, chat_id,
            f"{card}\n\nTier {tool_plan.tier} — reply '{prompt_word}' to run; "
            "/cancel to abort, /use <tool>, /why for the long version. "
            "(Approval expires in 5 min.)",
        )
        return

    # Tier 1 — autopilot
    await _send(client, chat_id, card)
    await _dispatch_and_reply(client, chat_id, job, tool_plan)


async def _dispatch_and_reply(client: httpx.AsyncClient, chat_id: int, job, plan=None) -> None:
    """Run the full dispatch pipeline and reply with the result.

    `plan` is the ToolPlan from the planner; passing it through means
    dispatch() honors the planner's primary_tool and model_recommendation.
    """
    from agent_os.orchestrator.adapters.job_router import dispatch
    try:
        result = await dispatch(job, plan=plan)
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
            "Plan-card overrides (after a plan is shown):\n"
            "  yes / YES   approve and run (YES required for Tier 3)\n"
            "  /cancel     abort the pending plan\n"
            "  /use <tool> [<model>]   swap the runtime / model\n"
            "  /why        explain how this plan was picked\n"
            "  /tier <1|2|3>   force a tier override\n\n"
            "Other commands:\n"
            "  /identity           show current persona + available options\n"
            "  /identity <name>    switch persona (e.g. /identity coo)\n"
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
            except (TimeoutError, httpx.HTTPError) as exc:
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
