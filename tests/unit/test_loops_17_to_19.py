"""Regression tests for loops 17-19."""
from __future__ import annotations

import os


# ---------- Loop 17: unbounded growth caps ----------

def test_a2a_task_store_evicts_oldest_when_over_cap(monkeypatch):
    monkeypatch.setenv("A2A_MAX_TASKS", "3")
    # Reload the module so the cap is picked up
    import importlib
    import agent_os.a2a.server as srv
    importlib.reload(srv)

    for i in range(5):
        t = srv.A2ATask(task_id=f"t{i}", message={})
        srv._store_task(t)

    assert len(srv._tasks) == 3, f"got {len(srv._tasks)} tasks, expected 3"
    assert "t0" not in srv._tasks
    assert "t1" not in srv._tasks
    assert {"t2", "t3", "t4"} == set(srv._tasks.keys())


# ---------- Loop 18: spawn failure cleanup ----------

def test_cleanup_hint_for_each_provider():
    from agent_os.orchestrator.spawner import _cleanup_hint
    assert "doctl" in _cleanup_hint("digitalocean", "12345", "1.2.3.4")
    assert "12345" in _cleanup_hint("digitalocean", "12345", "1.2.3.4")
    assert "hcloud" in _cleanup_hint("hetzner", "67890", "5.6.7.8")
    assert "67890" in _cleanup_hint("hetzner", "67890", "5.6.7.8")
    # Unknown provider falls through with the IP
    assert "1.2.3.4" in _cleanup_hint("aws", "i-0000", "1.2.3.4")


def test_patch_agent_status_updates_existing_entry(tmp_path, monkeypatch):
    """Round-trip: write a registry entry, patch its status, read it back."""
    import yaml
    from agent_os.orchestrator import spawner

    fake_root = tmp_path / "vault" / "projects"
    fake_root.mkdir(parents=True)
    registry_path = fake_root / "registry.yaml"
    registry_path.write_text(yaml.safe_dump({"agents": [
        {"id": "alpha", "status": "active", "tier": 2},
        {"id": "beta",  "status": "active", "tier": 1},
    ]}))

    monkeypatch.setattr(
        "agent_os.orchestrator.spawner.os.path.abspath",
        lambda p: str(registry_path),
    )
    spawner._patch_agent_status("alpha", "bootstrap_failed")

    out = yaml.safe_load(registry_path.read_text())
    statuses = {a["id"]: a["status"] for a in out["agents"]}
    assert statuses["alpha"] == "bootstrap_failed"
    assert statuses["beta"] == "active"


# ---------- Loop 19: hermes_self runtime exists ----------

def test_hermes_self_module_exists():
    """Without this module, dispatch crashes on every default-routed job."""
    import importlib
    mod = importlib.import_module("agent_os.runtimes.hermes_self.invoke")
    assert callable(mod.invoke)


def test_hermes_self_default_model_uses_env_chain(monkeypatch):
    monkeypatch.setenv("HERMES_DEFAULT_MODEL", "deepseek-chat")
    monkeypatch.delenv("COORDINATOR_DEFAULT_MODEL", raising=False)
    from agent_os.runtimes.hermes_self import invoke as inv
    assert inv._default_model() == "deepseek-chat"

    monkeypatch.delenv("HERMES_DEFAULT_MODEL", raising=False)
    monkeypatch.setenv("COORDINATOR_DEFAULT_MODEL", "claude-opus-4-7")
    assert inv._default_model() == "claude-opus-4-7"

    monkeypatch.delenv("COORDINATOR_DEFAULT_MODEL", raising=False)
    assert inv._default_model() == "claude-sonnet-4-5"  # final fallback


def test_hermes_self_routes_claude_to_anthropic():
    """Sanity: prefix routing is wired correctly so we don't accidentally
    send claude- prompts through OpenRouter."""
    import inspect
    from agent_os.runtimes.hermes_self import invoke as inv
    src = inspect.getsource(inv._call_llm)
    assert 'startswith("claude-")' in src
    assert "_call_anthropic" in src
