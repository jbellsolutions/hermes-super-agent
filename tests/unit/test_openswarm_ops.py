"""Phase C + D coverage:

- cost_rollup, hibernate_idle, snapshot_json, BudgetExceeded gate
- pipeline (sequential cross-swarm), fan_out (parallel)
- upgrader stream + smoke harness + daemon registration
- Slack /build-swarm + /list-swarms slash commands
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml


@pytest.fixture
def synthetic_vendor(tmp_path: Path) -> Path:
    vendor = tmp_path / "vendor-openswarm"
    vendor.mkdir()
    (vendor / "swarm.py").write_text("# fake swarm.py\n")
    (vendor / "server.py").write_text("# fake server.py\n")
    (vendor / "AGENTS.md").write_text("# AGENTS.md\nFake.\n")
    (vendor / ".env.example").write_text("OPENAI_API_KEY=replace-me\n")
    (vendor / "shared_instructions.md").write_text("# shared\n")
    for agent in ("orchestrator", "deep_research", "docs_agent"):
        folder = vendor / agent
        folder.mkdir()
        (folder / "instructions.md").write_text(f"# {agent}\n")
    return vendor


@pytest.fixture
def isolated(tmp_path: Path, synthetic_vendor: Path,
             monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    monkeypatch.setenv("OPENSWARM_REGISTRY", str(tmp_path / "registry.yaml"))
    monkeypatch.setenv("OPENSWARM_HOME", str(tmp_path / "swarms"))
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path / "vault"))
    monkeypatch.setenv("OPENSWARM_VENDOR_ROOT", str(synthetic_vendor))
    monkeypatch.setenv("OPENSWARM_PORT_LOW", "9300")
    monkeypatch.setenv("OPENSWARM_PORT_HIGH", "9309")
    monkeypatch.setenv("OPENSWARM_IDLE_HIBERNATE_MIN", "0")
    import importlib

    from agent_os.channels.slack import swarm_commands
    from agent_os.runtimes import _base as runtime_base
    from agent_os.runtimes.openswarm import (
        builder,
        customizers,
        fleet,
        invoke,
        ports,
        registry,
        skills,
        validators,
    )
    from agent_os.upgrader.smoke import openswarm as smoke_openswarm
    from agent_os.upgrader.streams import openswarm as stream_openswarm
    importlib.reload(runtime_base)
    importlib.reload(registry)
    importlib.reload(ports)
    importlib.reload(skills)
    importlib.reload(fleet)
    importlib.reload(customizers)
    importlib.reload(validators)
    importlib.reload(builder)
    importlib.reload(invoke)
    importlib.reload(smoke_openswarm)
    importlib.reload(stream_openswarm)
    importlib.reload(swarm_commands)
    return {
        "vendor": synthetic_vendor,
        "registry": tmp_path / "registry.yaml",
        "swarms": tmp_path / "swarms",
        "vault": tmp_path / "vault",
    }


# ============================================================
# cost rollup + budget gate
# ============================================================

_ARTIFACT_SEQ = [0]


def _write_artifact(vault_root: Path, swarm: str, *, cost: float = 0.0,
                    age_days: float = 0.0) -> Path:
    runs = vault_root / "runs" / "openswarm"
    runs.mkdir(parents=True, exist_ok=True)
    _ARTIFACT_SEQ[0] += 1
    name = f"{int(1e6 * (age_days + 1))}-{_ARTIFACT_SEQ[0]:04d}-{swarm}.yaml"
    path = runs / name
    path.write_text(yaml.safe_dump({
        "runtime": "openswarm",
        "job_id": f"job-{swarm}-{_ARTIFACT_SEQ[0]}",
        "status": "ok",
        "output": {"swarm": swarm, "agent": "auto", "port": 1234,
                   "response": {"cost_usd": cost}},
        "cost_usd": 0.0,
        "latency_ms": 100,
    }))
    if age_days:
        ts = path.stat().st_mtime - age_days * 86400
        os.utime(path, (ts, ts))
    return path


def test_cost_rollup_empty_returns_zero(isolated):
    from agent_os.runtimes.openswarm import fleet
    result = fleet.cost_rollup("seo-swarm", days=1)
    assert result["cost_usd"] == 0.0
    assert result["runs"] == 0


def test_cost_rollup_aggregates_per_swarm(isolated):
    from agent_os.runtimes.openswarm import fleet
    _write_artifact(isolated["vault"], "seo-swarm", cost=0.50)
    _write_artifact(isolated["vault"], "seo-swarm", cost=0.25)
    _write_artifact(isolated["vault"], "default", cost=0.10)
    result = fleet.cost_rollup(days=1)
    assert result["swarms"]["seo-swarm"]["cost_usd"] == pytest.approx(0.75)
    assert result["swarms"]["seo-swarm"]["runs"] == 2
    assert result["swarms"]["default"]["cost_usd"] == pytest.approx(0.10)


def test_cost_rollup_window_excludes_old(isolated):
    from agent_os.runtimes.openswarm import fleet
    _write_artifact(isolated["vault"], "x", cost=1.0, age_days=2)
    _write_artifact(isolated["vault"], "x", cost=0.5, age_days=0)
    result = fleet.cost_rollup("x", days=1)
    assert result["cost_usd"] == pytest.approx(0.5)
    result7 = fleet.cost_rollup("x", days=7)
    assert result7["cost_usd"] == pytest.approx(1.5)


def test_run_pre_flight_warns_at_soft_threshold(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("warn-swarm", port=9301, agency="open-swarm",
                 cost_budget_daily_usd=1.0, pid=os.getpid())
    _write_artifact(isolated["vault"], "warn-swarm", cost=0.85)
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True), \
         patch("agent_os.runtimes.openswarm.fleet.http_client.get_completion",
               return_value={"text": "ok"}):
        result = fleet.run(swarm="warn-swarm", prompt="hi")
    assert "cost_warning" in result
    assert "0.85" in result["cost_warning"]


def test_run_pre_flight_blocks_at_budget(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    from agent_os.runtimes.openswarm.fleet import BudgetExceeded
    registry.add("block-swarm", port=9301, agency="open-swarm",
                 cost_budget_daily_usd=1.0, pid=os.getpid())
    _write_artifact(isolated["vault"], "block-swarm", cost=1.5)
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True):
        with pytest.raises(BudgetExceeded):
            fleet.run(swarm="block-swarm", prompt="hi")


def test_run_pre_flight_silent_below_threshold(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("ok-swarm", port=9301, agency="open-swarm",
                 cost_budget_daily_usd=10.0, pid=os.getpid())
    _write_artifact(isolated["vault"], "ok-swarm", cost=1.0)  # 10% only
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health", return_value=True), \
         patch("agent_os.runtimes.openswarm.fleet.http_client.get_completion",
               return_value={"text": "ok"}):
        result = fleet.run(swarm="ok-swarm", prompt="hi")
    assert "cost_warning" not in result


# ============================================================
# idle hibernation
# ============================================================

def test_hibernate_idle_disabled_by_default(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("idle-swarm", port=9301, pid=os.getpid(),
                 last_run="2020-01-01T00:00:00")  # very stale
    out = fleet.hibernate_idle()
    assert "idle-swarm" in out["skipped"]
    assert "idle-swarm" not in out["hibernated"]


def test_hibernate_idle_stops_stale_swarm(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("stale", port=9301, pid=os.getpid(),
                 idle_hibernate_minutes=30,
                 last_run=(dt.datetime.now(dt.UTC) - dt.timedelta(hours=2))
                 .isoformat(timespec="seconds"))
    with patch("agent_os.runtimes.openswarm.fleet.stop") as stop:
        out = fleet.hibernate_idle()
    assert out["hibernated"] == ["stale"]
    stop.assert_called_once_with("stale")


def test_hibernate_idle_skips_recent_swarm(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("fresh", port=9301, pid=os.getpid(),
                 idle_hibernate_minutes=30,
                 last_run=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))
    with patch("agent_os.runtimes.openswarm.fleet.stop") as stop:
        out = fleet.hibernate_idle()
    assert out["hibernated"] == []
    stop.assert_not_called()


def test_hibernate_idle_skips_stopped_swarm(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("stopped", port=9301, pid=None,
                 idle_hibernate_minutes=30,
                 last_run="2020-01-01T00:00:00+00:00")
    with patch("agent_os.runtimes.openswarm.fleet.stop") as stop:
        out = fleet.hibernate_idle()
    assert out["hibernated"] == []
    stop.assert_not_called()


# ============================================================
# snapshot_json + dashboard payload
# ============================================================

def test_snapshot_json_writes_to_vault(isolated):
    import json

    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("a", port=9301, agency="open-swarm",
                 business_purpose="general", customizer="manual",
                 cost_budget_daily_usd=10.0, pid=os.getpid())
    _write_artifact(isolated["vault"], "a", cost=2.50)
    with patch("agent_os.runtimes.openswarm.fleet.http_client.health",
               return_value=True):
        snap = fleet.snapshot_json()
    assert snap["fleet"][0]["name"] == "a"
    assert snap["fleet"][0]["live_status"] == "running"
    assert snap["fleet"][0]["cost_today_usd"] == pytest.approx(2.50)
    assert snap["fleet"][0]["runs_today"] == 1
    path = Path(snap["written_to"])
    assert path.exists()
    persisted = json.loads(path.read_text())
    assert persisted["fleet"][0]["name"] == "a"


def test_snapshot_json_no_write(isolated):
    from agent_os.runtimes.openswarm import fleet
    snap = fleet.snapshot_json(write=False)
    assert "written_to" not in snap
    assert "generated_at" in snap


# ============================================================
# pipeline
# ============================================================

def test_pipeline_threads_prev_into_next(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("a", port=9301, pid=os.getpid())
    registry.add("b", port=9302, pid=os.getpid())

    seen_prompts: list[str] = []

    def fake_run(*, swarm, agent, prompt, files):
        seen_prompts.append(prompt)
        return {"swarm": swarm, "agent": agent, "port": 9301,
                "response": {"text": f"{swarm}-output"}}

    with patch("agent_os.runtimes.openswarm.fleet.run", side_effect=fake_run):
        out = fleet.pipeline([
            {"swarm": "a", "prompt": "first"},
            {"swarm": "b", "prompt": "use {prev}"},
        ])
    assert seen_prompts == ["first", "use a-output"]
    assert out["final"]["swarm"] == "b"
    assert len(out["steps"]) == 2


def test_pipeline_empty_returns_empty(isolated):
    from agent_os.runtimes.openswarm import fleet
    out = fleet.pipeline([])
    assert out == {"steps": [], "final": None}


def test_pipeline_handles_string_response(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("x", port=9301, pid=os.getpid())

    seen: list[str] = []

    def fake_run(*, swarm, agent, prompt, files):
        seen.append(prompt)
        return {"swarm": swarm, "agent": agent, "port": 9301, "response": "raw-string"}

    with patch("agent_os.runtimes.openswarm.fleet.run", side_effect=fake_run):
        fleet.pipeline([
            {"swarm": "x", "prompt": "first"},
            {"swarm": "x", "prompt": "got {prev}"},
        ])
    assert seen[1] == "got raw-string"


# ============================================================
# fan_out
# ============================================================

def test_fan_out_preserves_order(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("p", port=9301, pid=os.getpid())

    def fake_run(*, swarm, agent, prompt, files):
        return {"swarm": swarm, "prompt": prompt, "response": {"text": prompt.upper()}}

    with patch("agent_os.runtimes.openswarm.fleet.run", side_effect=fake_run):
        out = fleet.fan_out(swarm="p", prompts=["a", "b", "c", "d"], concurrency=2)
    assert [r["prompt"] for r in out["results"]] == ["a", "b", "c", "d"]
    assert out["errors"] == []


def test_fan_out_collects_per_prompt_errors(isolated):
    from agent_os.runtimes.openswarm import fleet, registry
    registry.add("e", port=9301, pid=os.getpid())

    def fake_run(*, swarm, agent, prompt, files):
        if prompt == "boom":
            raise RuntimeError("nope")
        return {"swarm": swarm, "prompt": prompt}

    with patch("agent_os.runtimes.openswarm.fleet.run", side_effect=fake_run):
        out = fleet.fan_out(swarm="e", prompts=["ok", "boom", "ok2"])
    assert out["results"][0]["prompt"] == "ok"
    assert "error" in out["results"][1]
    assert out["results"][2]["prompt"] == "ok2"
    assert len(out["errors"]) == 1
    assert out["errors"][0]["prompt_index"] == 1


def test_fan_out_empty_prompts(isolated):
    from agent_os.runtimes.openswarm import fleet
    out = fleet.fan_out(swarm="p", prompts=[])
    assert out == {"results": [], "errors": []}


# ============================================================
# invoke dispatcher — new ops
# ============================================================

def test_invoke_cost(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    _write_artifact(isolated["vault"], "x", cost=0.5)
    result = inv.invoke({"op": "cost", "swarm": "x"})
    assert result.status == "ok"
    assert result.output["cost_usd"] == pytest.approx(0.5)


def test_invoke_hibernate(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    result = inv.invoke({"op": "hibernate"})
    assert result.status == "ok"
    assert "hibernated" in result.output


def test_invoke_snapshot_writes_file(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    from agent_os.runtimes.openswarm import registry
    registry.add("x", port=9301, agency="open-swarm")
    result = inv.invoke({"op": "snapshot"})
    assert result.status == "ok"
    assert Path(result.output["written_to"]).exists()


def test_invoke_pipeline(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    from agent_os.runtimes.openswarm import registry
    registry.add("a", port=9301, pid=os.getpid())
    with patch("agent_os.runtimes.openswarm.fleet.run") as run_mock:
        run_mock.return_value = {"swarm": "a", "response": {"text": "x"}}
        result = inv.invoke({"op": "pipeline",
                             "steps": [{"swarm": "a", "prompt": "first"}]})
    assert result.status == "ok"
    assert result.output["final"]["swarm"] == "a"


def test_invoke_fan_out(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    from agent_os.runtimes.openswarm import registry
    registry.add("a", port=9301, pid=os.getpid())
    with patch("agent_os.runtimes.openswarm.fleet.run") as run_mock:
        run_mock.return_value = {"swarm": "a", "response": "ok"}
        result = inv.invoke({"op": "fan_out", "swarm": "a",
                             "prompts": ["x", "y"]})
    assert result.status == "ok"
    assert len(result.output["results"]) == 2


# ============================================================
# upgrader stream + smoke
# ============================================================

def test_smoke_passes_on_clean_vendor_no_swarms(isolated):
    from agent_os.upgrader.smoke.openswarm import smoke
    assert smoke() is True


def test_smoke_fails_when_vendor_missing_required_files(isolated, monkeypatch):
    from agent_os.upgrader.smoke.openswarm import smoke
    (isolated["vendor"] / "swarm.py").unlink()
    assert smoke() is False


def test_smoke_passes_with_default_swarm_in_state(isolated):
    from agent_os.runtimes.openswarm import builder, skills
    from agent_os.upgrader.smoke.openswarm import smoke
    builder.build("default-test", "x", customizer="noop", validator="noop")
    # smoke checks for {name}-swarm.md skill
    assert (skills.ACTIVE_DIR / "default-test-swarm.md").exists()
    assert smoke() is True


def test_smoke_fails_when_swarm_folder_vanishes(isolated):
    import shutil

    from agent_os.runtimes.openswarm import builder, fleet
    from agent_os.upgrader.smoke.openswarm import smoke
    builder.build("ghost", "x", customizer="noop", validator="noop")
    shutil.rmtree(fleet.folder_for("ghost"))
    assert smoke() is False


def test_smoke_replays_manual_customizer(isolated):
    from agent_os.runtimes.openswarm import builder
    from agent_os.upgrader.smoke.openswarm import smoke
    builder.build(
        "replay", "x",
        customizer="manual",
        customizer_options={"shared_context": "specialized.\n"},
        validator="noop",
    )
    # Replay re-runs the manual customizer against a fresh vendor in /tmp.
    # ManualCustomizer is deterministic, so smoke should pass.
    assert smoke() is True


def test_upgrader_stream_module_loads(isolated):
    from agent_os.upgrader.streams import openswarm as s
    assert callable(s.run)


def test_daemon_includes_openswarm_stream():
    from agent_os.upgrader import daemon
    names = [n for n, _ in daemon.STREAMS]
    assert "openswarm" in names
    # ensure it sits next to other agent runtimes, not at the very end
    assert names.index("openswarm") < names.index("vendor_health")


# ============================================================
# Slack /build-swarm + /list-swarms
# ============================================================

def test_parse_build_args_minimal(isolated):
    from agent_os.channels.slack.swarm_commands import parse_build_args
    args = parse_build_args("seo-swarm -- SEO research and writing")
    assert args == {"name": "seo-swarm", "description": "SEO research and writing"}


def test_parse_build_args_with_options(isolated):
    from agent_os.channels.slack.swarm_commands import parse_build_args
    args = parse_build_args(
        'ops-swarm customizer=manual validator=noop cost_budget_daily_usd=5 -- "ops content"'
    )
    assert args["name"] == "ops-swarm"
    assert args["customizer"] == "manual"
    assert args["validator"] == "noop"
    assert args["cost_budget_daily_usd"] == 5.0
    assert args["description"] == "ops content"


def test_parse_build_args_missing_dashdash(isolated):
    from agent_os.channels.slack.swarm_commands import CommandError, parse_build_args
    with pytest.raises(CommandError, match="Description required"):
        parse_build_args("seo-swarm SEO research")


def test_parse_build_args_empty_description(isolated):
    from agent_os.channels.slack.swarm_commands import CommandError, parse_build_args
    with pytest.raises(CommandError, match="non-empty"):
        parse_build_args("seo-swarm --   ")


def test_parse_build_args_missing_name(isolated):
    from agent_os.channels.slack.swarm_commands import CommandError, parse_build_args
    with pytest.raises(CommandError, match="name required"):
        parse_build_args("-- description")


def test_parse_build_args_unknown_option(isolated):
    from agent_os.channels.slack.swarm_commands import CommandError, parse_build_args
    with pytest.raises(CommandError, match="unknown option"):
        parse_build_args("x foo=bar -- desc")


def test_parse_build_args_bad_budget(isolated):
    from agent_os.channels.slack.swarm_commands import CommandError, parse_build_args
    with pytest.raises(CommandError, match="numeric"):
        parse_build_args("x cost_budget_daily_usd=oops -- desc")


def test_handle_build_command_happy_path(isolated):
    from agent_os.channels.slack.swarm_commands import handle_command
    payload = {
        "command": "/build-swarm",
        "text": "slack-swarm customizer=noop validator=noop -- via slack",
        "user_id": "U123",
    }
    response = handle_command(payload)
    assert response["response_type"] == "in_channel"
    assert "slack-swarm" in response["text"]
    assert ":white_check_mark:" in response["text"]


def test_handle_build_command_parse_error(isolated):
    from agent_os.channels.slack.swarm_commands import handle_command
    response = handle_command({"command": "/build-swarm", "text": "bad input"})
    assert response["response_type"] == "ephemeral"
    assert ":warning:" in response["text"]


def test_handle_list_swarms(isolated):
    from agent_os.channels.slack.swarm_commands import handle_command
    from agent_os.runtimes.openswarm import registry
    registry.add("alpha", port=9301, agency="open-swarm",
                 business_purpose="general production")
    response = handle_command({"command": "/list-swarms", "text": ""})
    assert response["response_type"] == "in_channel"
    assert "alpha" in response["text"]
    assert "general production" in response["text"]


def test_handle_list_swarms_empty(isolated):
    from agent_os.channels.slack.swarm_commands import handle_command
    response = handle_command({"command": "/list-swarms", "text": ""})
    assert response["response_type"] == "ephemeral"
    assert "empty" in response["text"].lower()


def test_handle_unknown_command(isolated):
    from agent_os.channels.slack.swarm_commands import handle_command
    response = handle_command({"command": "/wat", "text": ""})
    assert response["response_type"] == "ephemeral"
    assert "Unknown command" in response["text"]


def test_slack_module_exports_on_slash_command(isolated):
    from agent_os.channels import slack
    assert hasattr(slack, "on_slash_command")
    assert callable(slack.on_slash_command)
