"""Loop 20 — contract tests for the seven Codex architecture fixes.

These tests pin the integration contracts that the F1–F7 fixes establish,
so future refactors can't silently break them.

  F1: A2A POST /messages actually runs dispatch() (not just plan).
  F2: dispatch() honors plan.primary_tool / model_recommendation.
  F3: a2a_delegate uses plain REST envelope, not JSON-RPC.
  F4: Telegram bot wires /cancel /use /why /tier into plan_overrides.
  F5: route() sends email/outbound-email/instantly tags to retell_channel.
  F6: hermes_self + coordinator share the same default model + honor
      model_recommendation.
  F7: HERMES_ROLE=worker prevents the spawned VPS from running the
      Telegram long-poller.
"""
from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest


# ---------- F2 + F5 ----------

def test_f2_dispatch_honors_plan_primary_tool(monkeypatch):
    """plan.primary_tool overrides tag-based routing when it names a runtime."""
    from agent_os.orchestrator.adapters.job_router import Job, dispatch

    captured: dict[str, object] = {}

    def fake_invoke(job):
        captured["runtime"] = "claude_subagents"
        captured["model"] = job.metadata.get("model")
        return {"status": "completed"}

    fake_module = SimpleNamespace(invoke=fake_invoke)
    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: fake_module if name == "agent_os.runtimes.claude_subagents.invoke"
        else __import__(name, fromlist=["*"]),
    )

    plan = SimpleNamespace(
        primary_tool="claude_subagents",
        model_recommendation="claude-opus-4.7",
    )
    # Tags would route to "openswarm" if plan didn't override.
    job = Job(prompt="hi", tags={"swarm"})

    asyncio.run(dispatch(job, plan=plan))

    assert captured["runtime"] == "claude_subagents"
    assert captured["model"] == "claude-opus-4.7"


def test_f2_dispatch_falls_back_to_route_when_no_plan(monkeypatch):
    from agent_os.orchestrator.adapters.job_router import Job, dispatch

    seen: dict[str, str] = {}

    def fake_invoke(job):
        seen["runtime"] = "openswarm"
        return {"status": "completed"}

    fake_module = SimpleNamespace(invoke=fake_invoke)
    monkeypatch.setattr(
        "importlib.import_module",
        lambda name: fake_module if name == "agent_os.runtimes.openswarm.invoke"
        else __import__(name, fromlist=["*"]),
    )
    asyncio.run(dispatch(Job(prompt="x", tags={"swarm"})))
    assert seen["runtime"] == "openswarm"


def test_f5_route_sends_email_tags_to_retell_channel():
    from agent_os.orchestrator.adapters.job_router import Job, route
    for tag in ("email", "outbound-email", "cold-email", "instantly"):
        assert route(Job(prompt="x", tags={tag})) == "retell_channel", \
            f"tag {tag!r} should route to retell_channel"


def test_f5_route_still_sends_phone_tags_to_retell_channel():
    from agent_os.orchestrator.adapters.job_router import Job, route
    for tag in ("phone", "outbound-phone", "retell"):
        assert route(Job(prompt="x", tags={tag})) == "retell_channel"


# ---------- F1 ----------

def test_f1_a2a_dispatch_calls_dispatch(monkeypatch):
    """_dispatch_task must execute through dispatch(), not stop at route()."""
    from agent_os.a2a import server as srv

    called: dict[str, object] = {}

    async def fake_dispatch(job, plan=None):
        called["dispatched"] = True
        called["plan_primary"] = getattr(plan, "primary_tool", None)
        called["job_prompt"] = job.prompt
        return {"status": "completed", "text": "ok"}

    monkeypatch.setattr(
        "agent_os.orchestrator.adapters.job_router.dispatch",
        fake_dispatch,
    )
    monkeypatch.setattr(
        "agent_os.bus.nats_publisher.publish_event",
        lambda *a, **k: None,
    )

    task = srv.A2ATask(
        task_id="t1",
        message={"metadata": {"tags": "swarm"}},
    )
    asyncio.run(srv._dispatch_task(task, "build me a deck", "admiral"))

    assert called.get("dispatched") is True
    assert called.get("job_prompt") == "build me a deck"
    assert task.status == srv.TaskStatus.COMPLETED


def test_f1_a2a_tier3_blocks_without_confirmation(monkeypatch):
    """Tier 3 jobs must NOT auto-execute through /messages."""
    from agent_os.a2a import server as srv
    from agent_os.orchestrator import tool_planner

    async def fake_dispatch(job, plan=None):
        raise AssertionError("dispatch must not be called for tier 3")

    fake_plan = tool_planner.ToolPlan(
        task_summary="deploy prod",
        primary_tool="terminal",
        primary_reason="forced",
        tier=3,
        requires_explicit_confirm=True,
    )
    monkeypatch.setattr(
        "agent_os.orchestrator.tool_planner.plan",
        lambda job, **kw: fake_plan,
    )
    monkeypatch.setattr(
        "agent_os.orchestrator.adapters.job_router.dispatch",
        fake_dispatch,
    )
    monkeypatch.setattr(
        "agent_os.bus.nats_publisher.publish_event",
        lambda *a, **k: None,
    )

    task = srv.A2ATask(task_id="t-tier3", message={"metadata": {}})
    asyncio.run(srv._dispatch_task(task, "deploy prod", "admiral"))

    assert task.status == srv.TaskStatus.SUBMITTED
    assert task.result and task.result.get("needs_confirmation") is True


# ---------- F3 ----------

def test_f3_a2a_delegate_uses_plain_rest_envelope(monkeypatch):
    """a2a_delegate must POST {parts:[{kind,text}], taskId, metadata} — not JSON-RPC."""
    from agent_os.runtimes.a2a_delegate import invoke as inv

    captured: dict[str, object] = {}

    class FakeResp:
        status_code = 202
        def raise_for_status(self):
            return None
        def json(self):
            return {"taskId": "remote-1", "status": "submitted"}

    class FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            return False
        async def post(self, url, json=None):
            captured["url"] = url
            captured["payload"] = json
            return FakeResp()
        async def get(self, url):
            captured["poll_url"] = url
            class R:
                status_code = 200
                def raise_for_status(self): return None
                def json(self):
                    return {"status": {"state": "completed"},
                            "result": {"text": "done"}}
            return R()

    monkeypatch.setattr(inv.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(inv, "publish_event", lambda *a, **k: None)
    monkeypatch.setattr(inv, "_POLL_INTERVAL", 0)
    monkeypatch.setattr(inv, "_POLL_TIMEOUT", 1)

    job = SimpleNamespace(
        prompt="hello",
        tags={"a2a"},
        metadata={"a2a_endpoint": "http://localhost:9999"},
    )
    asyncio.run(inv.run(job))

    payload = captured["payload"]
    assert "jsonrpc" not in payload, "must NOT use JSON-RPC envelope"
    assert "method" not in payload
    assert "params" not in payload
    assert payload["parts"][0]["kind"] == "text"
    assert payload["parts"][0]["text"] == "hello"
    assert "taskId" in payload
    assert "metadata" in payload


# ---------- F4 ----------

def test_f4_telegram_handles_cancel_command():
    from agent_os.orchestrator.adapters import plan_overrides
    o = plan_overrides.parse("/cancel")
    assert o is not None and o.kind == "cancel"


def test_f4_telegram_handles_use_command():
    from agent_os.orchestrator.adapters import plan_overrides
    o = plan_overrides.parse("/use claude_subagents claude-opus-4.7")
    assert o is not None and o.kind == "use"
    assert o.tool == "claude_subagents"
    assert o.model == "claude-opus-4.7"


def test_f4_telegram_handles_why_and_tier():
    from agent_os.orchestrator.adapters import plan_overrides
    assert plan_overrides.parse("/why").kind == "why"
    assert plan_overrides.parse("/tier 3").tier == 3


def test_f4_plan_card_no_longer_advertises_phantom_grace():
    """plan_card text must not say 'proceeding in 3s' — channels need explicit yes."""
    from agent_os.orchestrator import plan_card, tool_planner
    plan = tool_planner.ToolPlan(
        task_summary="test",
        primary_tool="hermes_self",
        primary_reason="default",
        tier=2,
        grace_seconds=3,
        estimated_cost_usd=0.05,
        estimated_seconds=60,
    )
    out = plan_card.render_markdown(plan)
    assert "proceeding in" not in out
    assert "yes" in out.lower()


# ---------- F6 ----------

def test_f6_hermes_self_default_model_aligned_with_models_yaml(monkeypatch):
    monkeypatch.delenv("HERMES_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("COORDINATOR_DEFAULT_MODEL", raising=False)
    from agent_os.runtimes.hermes_self import invoke as inv
    # Final fallback must be a real entry in config/models.yaml — not the
    # phantom "claude-sonnet-4-5" the old default referenced.
    assert inv._default_model() == "claude-sonnet-4.7"


def test_f6_hermes_self_honors_model_recommendation(monkeypatch):
    """When metadata['model'] is unset, fall back to model_recommendation."""
    from agent_os.runtimes.hermes_self import invoke as inv

    captured: dict[str, str] = {}

    def fake_call(model, prompt):
        captured["model"] = model
        return "ok"

    monkeypatch.setattr(inv, "_call_llm", fake_call)
    monkeypatch.setattr(inv, "write_run_artifact", lambda r: None)

    job = SimpleNamespace(
        prompt="hi",
        metadata={"model_recommendation": "kimi-k2"},
    )
    inv.invoke(job)
    assert captured["model"] == "kimi-k2"


def test_f6_coordinator_runtime_select_model_priority():
    from agent_os.runtimes.coordinator.invoke import _select_model
    from agent_os.orchestrator.adapters.job_router import Job

    # 1. coordinator_model wins over everything
    j = Job(prompt="x", metadata={
        "coordinator_model": "kimi-k2",
        "model_recommendation": "claude-opus-4.7",
        "model": "gpt-5.5",
    })
    assert _select_model(j) == "kimi-k2"

    # 2. model_recommendation wins over generic model
    j = Job(prompt="x", metadata={
        "model_recommendation": "claude-opus-4.7",
        "model": "gpt-5.5",
    })
    assert _select_model(j) == "claude-opus-4.7"

    # 3. plain model still works
    j = Job(prompt="x", metadata={"model": "gpt-5.5"})
    assert _select_model(j) == "gpt-5.5"


# ---------- F7 ----------

def test_f7_worker_role_does_not_start_telegram_bot(monkeypatch):
    """HERMES_ROLE=worker keeps the lifespan from spawning the Telegram poller."""
    monkeypatch.setenv("HERMES_ROLE", "worker")

    from agent_os.a2a import server as srv

    started: list[str] = []

    async def trap_run_bot():
        started.append("telegram")

    async def trap_alert_forwarder():
        started.append("alerts")

    monkeypatch.setattr(
        "agent_os.channels.telegram.bot.run_bot", trap_run_bot
    )
    monkeypatch.setattr(
        "agent_os.channels.telegram.bot.run_alert_forwarder", trap_alert_forwarder
    )

    app = srv.create_a2a_app(agent_id="cold-email-superagent")
    if app is None:
        pytest.skip("fastapi not installed in this environment")

    async def drive_lifespan():
        async with app.router.lifespan_context(app):
            await asyncio.sleep(0.05)

    asyncio.run(drive_lifespan())

    assert started == [], f"worker role must not spawn telegram tasks; got {started}"


def test_f7_admiral_role_does_start_telegram_bot(monkeypatch):
    monkeypatch.setenv("HERMES_ROLE", "admiral")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")  # so run_bot returns immediately

    from agent_os.a2a import server as srv

    started: list[str] = []

    async def trap_run_bot():
        started.append("telegram")

    async def trap_alert_forwarder():
        started.append("alerts")

    monkeypatch.setattr(
        "agent_os.channels.telegram.bot.run_bot", trap_run_bot
    )
    monkeypatch.setattr(
        "agent_os.channels.telegram.bot.run_alert_forwarder", trap_alert_forwarder
    )

    app = srv.create_a2a_app(agent_id="admiral")
    if app is None:
        pytest.skip("fastapi not installed in this environment")

    async def drive_lifespan():
        async with app.router.lifespan_context(app):
            await asyncio.sleep(0.05)

    asyncio.run(drive_lifespan())

    assert "telegram" in started
    assert "alerts" in started
