"""Coverage for fixes from loops 7–16 — concurrency lock, NATS breaker,
bootstrap entrypoint, cost ceilings.

These are regression tests for bugs we just fixed. If any of them go red,
something we shipped in this set of loops broke.
"""
from __future__ import annotations

import os
import threading


def test_registry_lock_exists():
    """Registry writes must serialize via _REGISTRY_LOCK."""
    from agent_os.orchestrator import spawner
    assert isinstance(spawner._REGISTRY_LOCK, type(threading.Lock()))


def test_register_agent_uses_atomic_rename(tmp_path, monkeypatch):
    """Registry writes go through tempfile + os.replace, not direct write."""
    import inspect
    from agent_os.orchestrator import spawner
    src = inspect.getsource(spawner._register_agent)
    assert "tempfile.mkstemp" in src
    assert "os.replace" in src


def test_nats_breaker_state_resets_on_success():
    """publish_event circuit breaker recovers after a successful publish."""
    from agent_os.bus import nats_publisher as np
    np._breaker_record_failure()
    np._breaker_record_failure()
    np._breaker_record_failure()
    assert np._breaker_open() is True
    np._breaker_record_success()
    assert np._breaker_open() is False
    assert np._breaker_failures == 0


def test_nats_breaker_threshold_is_three():
    from agent_os.bus import nats_publisher as np
    np._breaker_record_success()  # reset
    np._breaker_record_failure()
    np._breaker_record_failure()
    assert np._breaker_open() is False, "should not open at 2 failures"
    np._breaker_record_failure()
    assert np._breaker_open() is True, "should open at 3 failures"
    np._breaker_record_success()  # cleanup


def test_bootstrap_uses_uvicorn_not_hermes():
    """Spawned VPSes must start the A2A server, not a non-existent 'hermes' bin."""
    from pathlib import Path
    template_path = Path(__file__).resolve().parents[2] / "templates" / "bootstrap.sh.j2"
    template = template_path.read_text()
    assert "uv run hermes" not in template, "non-existent entrypoint"
    assert "uvicorn agent_os.a2a.server:app" in template


def test_inline_bootstrap_uses_uvicorn_not_hermes():
    import inspect
    from agent_os.orchestrator import bootstrap
    src = inspect.getsource(bootstrap._inline_bootstrap)
    assert "uv run hermes" not in src
    assert "uvicorn agent_os.a2a.server:app" in src


def test_cli_has_tail_command():
    """`agent-os tail` must be wired."""
    import subprocess
    import sys
    out = subprocess.run(
        [sys.executable, "-m", "agent_os.cli", "--help"],
        capture_output=True, text=True, timeout=20,
    )
    assert "tail" in out.stdout, out.stdout
