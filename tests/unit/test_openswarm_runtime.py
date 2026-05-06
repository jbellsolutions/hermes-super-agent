"""openswarm runtime: registry, ports, fleet, invoke, skills.

These tests isolate every filesystem path via env vars and mock the HTTP
client + subprocess + signal interactions. No real OpenSwarm boot.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# pytest-asyncio's "auto" mode wraps any coroutine; nothing here is async.


# ---------- shared fixtures ----------

@pytest.fixture
def isolated_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    registry_path = tmp_path / "registry.yaml"
    swarms_home = tmp_path / "swarms"
    vault_root = tmp_path / "vault"
    monkeypatch.setenv("OPENSWARM_REGISTRY", str(registry_path))
    monkeypatch.setenv("OPENSWARM_HOME", str(swarms_home))
    monkeypatch.setenv("VAULT_ROOT", str(vault_root))
    monkeypatch.setenv("OPENSWARM_PORT_LOW", "9100")
    monkeypatch.setenv("OPENSWARM_PORT_HIGH", "9105")
    # reload modules so they pick up the env
    import importlib

    from agent_os.runtimes import _base as runtime_base
    from agent_os.runtimes.openswarm import fleet, invoke, ports, registry, skills
    importlib.reload(runtime_base)
    importlib.reload(registry)
    importlib.reload(ports)
    importlib.reload(skills)
    importlib.reload(fleet)
    importlib.reload(invoke)
    return {"registry": registry_path, "swarms_home": swarms_home, "vault": vault_root}


# ---------- registry ----------

def test_registry_add_get_remove(isolated_paths):
    from agent_os.runtimes.openswarm import registry
    registry.add("seo-swarm", port=9101, agency="open-swarm")
    entry = registry.get("seo-swarm")
    assert entry["port"] == 9101
    assert entry["agency"] == "open-swarm"
    assert "created_at" in entry

    registry.update("seo-swarm", pid=12345)
    assert registry.get("seo-swarm")["pid"] == 12345

    registry.remove("seo-swarm")
    assert registry.get("seo-swarm") is None


def test_registry_add_duplicate_raises(isolated_paths):
    from agent_os.runtimes.openswarm import registry
    registry.add("dup", port=9101)
    with pytest.raises(ValueError, match="already exists"):
        registry.add("dup", port=9102)


def test_registry_used_ports(isolated_paths):
    from agent_os.runtimes.openswarm import registry
    registry.add("a", port=9101)
    registry.add("b", port=9102)
    assert registry.used_ports() == {9101, 9102}


# ---------- ports ----------

def test_ports_skips_used_in_registry(isolated_paths):
    from agent_os.runtimes.openswarm import ports, registry
    registry.add("x", port=9100)
    registry.add("y", port=9101)
    assert ports.allocate("z") == 9102


def test_ports_exhausts_range(isolated_paths):
    from agent_os.runtimes.openswarm import ports, registry
    for i, name in enumerate(["a", "b", "c", "d", "e", "f"]):
        registry.add(name, port=9100 + i)
    with pytest.raises(RuntimeError, match="no free ports"):
        ports.allocate("g")


# ---------- skills ----------

def test_skills_render_default(isolated_paths):
    from agent_os.runtimes.openswarm import skills
    out = skills.render_default(manifest_path="vendor/openswarm")
    assert out.exists()
    text = out.read_text()
    assert "name: default-swarm" in text
    assert "runtime: openswarm" in text
    assert "swarm: default" in text


def test_skills_render_for(isolated_paths):
    from agent_os.runtimes.openswarm import skills
    out = skills.render_for(
        "seo-swarm",
        description="Use when SEO.",
        business_purpose="SEO research and writing",
        output_types="blog posts",
        examples=["Write a post about X."],
        cost_budget_daily_usd=10.0,
        manifest_path="~/.agent-os/swarms/seo-swarm/manifest.yaml",
    )
    text = out.read_text()
    assert "name: seo-swarm-swarm" in text
    assert "Use when SEO." in text
    assert "- Write a post about X." in text


def test_skills_remove_for(isolated_paths):
    from agent_os.runtimes.openswarm import skills
    skills.render_default()
    assert skills.remove_for("default") is True
    assert skills.remove_for("default") is False  # idempotent


# ---------- fleet ----------

def test_fleet_list_empty(isolated_paths):
    from agent_os.runtimes.openswarm import fleet
    assert fleet.list_swarms() == []


def test_fleet_run_missing_swarm_raises(isolated_paths):
    from agent_os.runtimes.openswarm import fleet
    with pytest.raises(KeyError):
        fleet.run(swarm="nope", prompt="x")


def test_fleet_run_calls_http(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("default", port=9101, agency="open-swarm", pid=os.getpid())
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True):
        with patch(
            "agent_os.runtimes.openswarm.fleet.http_client.get_completion",
            return_value={"text": "hello world"},
        ) as mocked:
            result = fleet.run(swarm="default", agent="auto", prompt="say hi")
    assert result["swarm"] == "default"
    assert result["port"] == 9101
    assert result["response"] == {"text": "hello world"}
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert kwargs["agency"] == "open-swarm"
    assert kwargs["message"] == "say hi"


def test_fleet_run_specific_agent_passes_through(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("default", port=9101, agency="open-swarm", pid=os.getpid())
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True):
        with patch(
            "agent_os.runtimes.openswarm.fleet.http_client.get_completion",
            return_value={"ok": True},
        ) as mocked:
            fleet.run(swarm="default", agent="slides_agent", prompt="x")
    assert mocked.call_args.kwargs["agent"] == "slides_agent"


def test_fleet_status_running_vs_crashed(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("alive", port=9101, pid=os.getpid())
    registry.add("dead", port=9102, pid=999999)  # implausibly high pid
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True):
        a = fleet.status("alive")
    assert a["live_status"] == "running"
    b = fleet.status("dead")
    assert b["live_status"] == "crashed"


def test_fleet_cleanup_orphans(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("orphan", port=9101, pid=999999)
    out = fleet.cleanup_orphans()
    assert out["reconciled"] == ["orphan"]
    assert registry.get("orphan")["pid"] is None


def test_fleet_destroy_archives(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    folder = fleet.folder_for("doomed")
    folder.mkdir(parents=True)
    (folder / "marker").write_text("hi")
    registry.add("doomed", port=9101, pid=None)

    out = fleet.destroy("doomed")

    assert registry.get("doomed") is None
    assert not folder.exists()
    archived = Path(out["archived_to"])
    assert archived.exists()
    assert (archived / "marker").read_text() == "hi"


def test_fleet_provision_default_creates_folder_and_registry(isolated_paths):
    from agent_os.runtimes.openswarm import fleet, registry
    entry = fleet.provision_default()
    assert entry["agency"] == "open-swarm"
    assert 9100 <= int(entry["port"]) <= 9105
    assert fleet.folder_for("default").exists()
    assert (fleet.folder_for("default") / "swarm.py").exists()  # copied from vendor
    assert registry.get("default") is not None


def test_fleet_provision_default_idempotent(isolated_paths):
    from agent_os.runtimes.openswarm import fleet
    a = fleet.provision_default()
    b = fleet.provision_default()
    assert a == b


# ---------- invoke dispatcher ----------

def test_invoke_run_routes_to_fleet(isolated_paths):
    from agent_os.runtimes.openswarm import invoke as inv
    from agent_os.runtimes.openswarm import registry
    registry.add("default", port=9101, agency="open-swarm", pid=os.getpid())
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True):
        with patch(
            "agent_os.runtimes.openswarm.fleet.http_client.get_completion",
            return_value={"answer": "42"},
        ):
            result = inv.invoke({"op": "run", "swarm": "default", "prompt": "?"})
    assert result.runtime == "openswarm"
    assert result.status == "ok"
    assert result.output["response"] == {"answer": "42"}


def test_invoke_list_returns_fleet(isolated_paths):
    from agent_os.runtimes.openswarm import invoke as inv
    from agent_os.runtimes.openswarm import registry
    registry.add("a", port=9101)
    registry.add("b", port=9102)
    result = inv.invoke({"op": "list"})
    assert result.status == "ok"
    names = {x["name"] for x in result.output}
    assert names == {"a", "b"}


def test_invoke_unknown_op_returns_error(isolated_paths):
    from agent_os.runtimes.openswarm import invoke as inv
    result = inv.invoke({"op": "wat"})
    assert result.status == "error"
    assert "unknown op" in result.error


def test_invoke_build_routes_to_builder(isolated_paths, monkeypatch):
    """op=build now reaches builder.build (Phase B done). Verifying dispatch
    only — full builder behavior is covered by tests/unit/test_openswarm_builder.py."""
    from agent_os.runtimes.openswarm import invoke as inv

    captured = {}

    def fake_build(name, description, **kwargs):
        captured["name"] = name
        captured["description"] = description
        captured["kwargs"] = kwargs
        return {"name": name, "ok": True}

    monkeypatch.setattr("agent_os.runtimes.openswarm.invoke.builder.build", fake_build)
    result = inv.invoke({
        "op": "build", "name": "x", "description": "y",
        "customizer": "noop", "validator": "noop",
    })
    assert result.status == "ok"
    assert captured == {
        "name": "x",
        "description": "y",
        "kwargs": {
            "customizer": "noop",
            "customizer_options": None,
            "validator": "noop",
            "cost_budget_daily_usd": 10.0,
        },
    }


def test_invoke_writes_run_artifact(isolated_paths):
    from agent_os.runtimes.openswarm import invoke as inv
    inv.invoke({"op": "list"})
    runs = isolated_paths["vault"] / "runs" / "openswarm"
    artifacts = list(runs.glob("*.yaml"))
    assert artifacts, "expected run artifact under vault/runs/openswarm/"


def test_invoke_handles_exceptions(isolated_paths):
    from agent_os.runtimes.openswarm import invoke as inv
    # missing required field "swarm" for status
    result = inv.invoke({"op": "destroy"})
    assert result.status == "error"
