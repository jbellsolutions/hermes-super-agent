"""Unit tests for the fabric runtimes (coordinator, retell, vps_spawn, a2a_delegate, agent_zero)."""
from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

import pytest

from agent_os.orchestrator.adapters.job_router import Job, dispatch, route


# ---------------------------------------------------------------------------
# Routing — tags map to the right fabric runtime
# ---------------------------------------------------------------------------

def test_fan_out_routes_to_coordinator():
    assert route(Job(prompt="fan out", tags={"fan-out"})) == "coordinator"


def test_coordinator_tag_routes_to_coordinator():
    assert route(Job(prompt="x", tags={"coordinator"})) == "coordinator"


def test_swarm_coordinator_tag_routes_to_coordinator():
    assert route(Job(prompt="x", tags={"swarm-coordinator"})) == "coordinator"


def test_spawn_superagent_routes_to_vps_spawn():
    assert route(Job(prompt="spin up", tags={"spawn-superagent"})) == "vps_spawn"


def test_build_specialist_routes_to_a2a_delegate():
    assert route(Job(prompt="build", tags={"build-specialist"})) == "a2a_delegate"


def test_phone_routes_to_retell():
    assert route(Job(prompt="call", tags={"phone"})) == "retell_channel"


def test_outbound_phone_routes_to_retell():
    assert route(Job(prompt="call", tags={"outbound-phone"})) == "retell_channel"


# ---------------------------------------------------------------------------
# Coordinator — model-pluggable selection
# ---------------------------------------------------------------------------

def test_coordinator_model_from_metadata(monkeypatch):
    from agent_os.runtimes.coordinator.invoke import _select_model
    monkeypatch.setenv("COORDINATOR_DEFAULT_MODEL", "claude-sonnet-4.7")
    job = Job(prompt="x", metadata={"coordinator_model": "deepseek-v4-pro"})
    assert _select_model(job) == "deepseek-v4-pro"


def test_coordinator_falls_back_to_env_default(monkeypatch):
    from agent_os.runtimes.coordinator.invoke import _select_model
    monkeypatch.setenv("COORDINATOR_DEFAULT_MODEL", "claude-sonnet-4.7")
    # Re-import to pick up the env var
    import importlib
    import agent_os.runtimes.coordinator.invoke as inv
    importlib.reload(inv)
    job = Job(prompt="x")
    assert inv._select_model(job) == "claude-sonnet-4.7"


def test_coordinator_no_model_when_unset(monkeypatch):
    monkeypatch.delenv("COORDINATOR_DEFAULT_MODEL", raising=False)
    import importlib
    import agent_os.runtimes.coordinator.invoke as inv
    importlib.reload(inv)
    job = Job(prompt="x")
    assert inv._select_model(job) == ""


def test_coordinator_local_fallback_when_url_unset(monkeypatch):
    """Without COORDINATOR_URL, should return a local fallback stub, not error."""
    monkeypatch.delenv("COORDINATOR_URL", raising=False)
    import importlib
    import agent_os.runtimes.coordinator.invoke as inv
    importlib.reload(inv)

    job = Job(prompt="research 50 startups")
    result = asyncio.run(inv.run(job))
    assert result["status"] == "completed"
    assert "local fallback" in result.get("note", "")


# ---------------------------------------------------------------------------
# Retell — tier 3 outbound dispatching is gated upstream; here just check stub
# ---------------------------------------------------------------------------

def test_retell_stubs_without_api_key(monkeypatch):
    monkeypatch.delenv("RETELL_API_KEY", raising=False)
    monkeypatch.delenv("INSTANTLY_API_KEY", raising=False)
    from agent_os.runtimes.retell_channel import invoke as inv
    job = Job(prompt="ring this number", tags={"phone"}, metadata={"phone_number": "+15551234567"})
    result = asyncio.run(inv.run(job))
    # Without API key, retell returns a dev-stub completed status with a stub note.
    assert result.get("status") in ("stub", "completed", "error")
    note = (result.get("note") or "") + (result.get("stub", "") or "")
    assert "stub" in note.lower() or result.get("status") == "stub"


# ---------------------------------------------------------------------------
# VPS spawn — without API token returns stub
# ---------------------------------------------------------------------------

def test_vps_provisioner_stubs_without_token(monkeypatch):
    monkeypatch.delenv("DO_API_TOKEN", raising=False)
    monkeypatch.delenv("HETZNER_API_TOKEN", raising=False)
    from agent_os.orchestrator import vps_provisioner
    result = asyncio.run(vps_provisioner.provision("test-agent"))
    assert result["status"] == "completed"
    assert result["provider"] == "stub"


# ---------------------------------------------------------------------------
# A2A delegate — without endpoint returns a stub note, not an error
# ---------------------------------------------------------------------------

def test_a2a_delegate_stubs_without_endpoint(monkeypatch):
    monkeypatch.delenv("ARCHON_A2A_URL", raising=False)
    import importlib
    import agent_os.runtimes.a2a_delegate.invoke as inv
    importlib.reload(inv)
    job = Job(prompt="build a linkedin specialist", tags={"build-specialist"})
    result = asyncio.run(inv.run(job))
    assert result["status"] == "stub"


# ---------------------------------------------------------------------------
# Agent Zero — without local server returns a stub
# ---------------------------------------------------------------------------

def test_agent_zero_stubs_when_unreachable(monkeypatch):
    # Point at a port nothing listens on
    monkeypatch.setenv("AGENT_ZERO_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("AGENT_ZERO_TIMEOUT", "1")
    import importlib
    import agent_os.runtimes.agent_zero.invoke as inv
    importlib.reload(inv)
    job = Job(prompt="open localhost", tags={"agent-zero"})
    result = inv.invoke(job)
    assert result.status == "stub"


# ---------------------------------------------------------------------------
# Dispatch table covers all RuntimeName entries
# ---------------------------------------------------------------------------

def test_dispatch_resolves_coordinator(monkeypatch):
    """Dispatch routes coordinator tag to coordinator.invoke.run."""
    monkeypatch.delenv("COORDINATOR_URL", raising=False)
    job = Job(prompt="fan out 50 things", tags={"fan-out"})
    result = asyncio.run(dispatch(job))
    assert result["status"] == "completed"
    assert "local fallback" in result.get("note", "")
