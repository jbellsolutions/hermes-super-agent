"""Composio module — offline behavior smoke tests.

Real network tests would live in tests/integration/test_composio_smoke.py and
only run when COMPOSIO_API_KEY is set. These tests verify the no-key path
returns clear, structured errors instead of crashing.
"""
from __future__ import annotations


def test_imports():
    from agent_os.composio import (  # noqa: F401
        call,
        connect,
        discover,
        is_configured,
        list_connections,
    )


def test_is_configured_false_without_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    from agent_os.composio import is_configured

    assert is_configured() is False


def test_call_without_key(monkeypatch, tmp_path):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path))
    from agent_os.composio import call

    result = call("slack_send_message", {"channel": "general", "text": "hi"})
    assert result.status == "not-configured"
    assert "COMPOSIO_API_KEY" in (result.error or "")


def test_discover_without_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    from agent_os.composio import discover

    assert discover("send a slack message") == []


def test_connect_without_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    from agent_os.composio import connect

    req = connect("slack")
    assert req.status == "not-configured"


def test_list_connections_empty_without_file(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path))
    from agent_os.composio import list_connections

    assert list_connections() == {}


def test_save_and_load_connections_round_trip(monkeypatch, tmp_path):
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path))
    from agent_os.composio.connect import _load_connections, _save_connections

    _save_connections({"slack": "conn-abc", "linear": "conn-xyz"})
    loaded = _load_connections()
    assert loaded == {"slack": "conn-abc", "linear": "conn-xyz"}
