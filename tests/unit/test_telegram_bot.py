"""Unit tests for the Telegram bot's testable bits.

We don't drive the long-poll loop here — that needs network. We do verify:
  - allowlist parsing
  - approval TTL/garbage collection
  - alert filter logic
  - event formatting
  - markdown-safety: no unescaped Markdown in send paths (we use plain text)
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest


def test_allowed_chats_parses_csv(monkeypatch):
    from agent_os.channels.telegram import bot
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123, 456,789")
    assert bot._allowed_chats() == {"123", "456", "789"}


def test_allowed_chats_empty_when_unset(monkeypatch):
    from agent_os.channels.telegram import bot
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert bot._allowed_chats() == set()


def test_gc_approvals_expires_old_entries():
    from agent_os.channels.telegram import bot
    bot._PENDING_APPROVALS.clear()
    bot._PENDING_APPROVALS[1] = {"job": object(), "expires_at": time.time() - 1}
    bot._PENDING_APPROVALS[2] = {"job": object(), "expires_at": time.time() + 600}
    bot._gc_approvals()
    assert 1 not in bot._PENDING_APPROVALS
    assert 2 in bot._PENDING_APPROVALS
    bot._PENDING_APPROVALS.clear()


def test_should_alert_forwards_alert_events():
    from agent_os.channels.telegram import bot
    e = SimpleNamespace(event_type="alert", agent_id="a", payload={})
    assert bot._should_alert(e) is True


def test_should_alert_forwards_needs_human():
    from agent_os.channels.telegram import bot
    e = SimpleNamespace(event_type="task.progress", agent_id="a",
                        payload={"needs_human": True})
    assert bot._should_alert(e) is True


def test_should_alert_forwards_task_failed():
    from agent_os.channels.telegram import bot
    e = SimpleNamespace(event_type="task.failed", agent_id="a", payload={})
    assert bot._should_alert(e) is True


def test_should_alert_skips_heartbeat_and_progress():
    from agent_os.channels.telegram import bot
    for et in ("heartbeat", "task.started", "task.completed", "task.progress"):
        e = SimpleNamespace(event_type=et, agent_id="a", payload={})
        assert bot._should_alert(e) is False, f"should not alert on {et}"


def test_format_event_compact_one_liner():
    from agent_os.channels.telegram import bot
    e = SimpleNamespace(
        event_type="task.failed",
        agent_id="cold-email-superagent",
        payload={"error": "API timeout", "task_id": "abc123"},
    )
    out = bot._format_event(e)
    assert "cold-email-superagent" in out
    assert "task.failed" in out
    assert "abc123" in out
    assert "API timeout" in out
    assert "\n" not in out, "should be a one-liner"


def test_max_body_chars_caps_message_size():
    """Hidden invariant: even a huge payload won't blow Telegram's 4096 limit."""
    from agent_os.channels.telegram import bot
    assert bot._MAX_BODY_CHARS < 4096


def test_no_markdown_parse_mode_in_send_path():
    """Bot uses plain text — verifies we don't accidentally re-introduce
    parse_mode='Markdown' which fails on user prompts containing _ * [ ].

    We check for the JSON-key form (with colon) so docstring mentions
    don't trip the test.
    """
    import inspect
    from agent_os.channels.telegram import bot
    src = inspect.getsource(bot._send)
    assert '"parse_mode":' not in src, "bot._send must not pass parse_mode in payload"
    assert "'parse_mode':" not in src


@pytest.mark.asyncio
async def test_handle_message_refuses_when_no_allowlist(monkeypatch):
    """Critical security invariant: empty TELEGRAM_CHAT_ID → ignore all messages."""
    from agent_os.channels.telegram import bot
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    sent: list[str] = []

    class FakeClient:
        async def post(self, *a, **kw):
            sent.append(str(kw))
            return SimpleNamespace(status_code=200)

    msg = {"chat": {"id": 999999}, "text": "hello"}
    await bot._handle_message(FakeClient(), msg)
    assert sent == [], "must not send anything when allowlist is empty"
