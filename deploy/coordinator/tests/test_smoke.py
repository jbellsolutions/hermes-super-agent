"""Smoke tests — exercise the routes without a real LLM call.

We monkeypatch ``coordinator.tasks.call_llm`` to a fast stub and verify the
fan-out wiring end-to-end: submit → state → poll → completed with artifacts.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    # Patch the LLM before the app imports it via tasks.py
    async def _fake_llm(model: str, prompt: str, system: str = "", max_tokens: int = 4096):
        from coordinator.llm import LLMResult
        return LLMResult(text=f"[{model}] {prompt[:30]}", model=model, input_tokens=10, output_tokens=20)

    from coordinator import tasks
    monkeypatch.setattr(tasks, "call_llm", _fake_llm)
    monkeypatch.setattr("coordinator.llm.call_llm", _fake_llm)

    from coordinator.main import app
    return TestClient(app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_agent_card_shape(client):
    card = client.get("/agentCard").json()
    assert card["name"] == "Hermes Coordinator"
    assert "fan_out" in {s["id"] for s in card["skills"]}


def test_submit_and_poll_single_prompt(client):
    resp = client.post(
        "/messages",
        json={
            "parts": [{"kind": "text", "text": "what is 2+2?"}],
            "metadata": {"model": "claude-sonnet-4-5"},
        },
    )
    assert resp.status_code == 200
    task_id = resp.json()["taskId"]

    # Poll until done (the fake LLM finishes immediately)
    for _ in range(50):
        out = client.get(f"/tasks/{task_id}").json()
        if out["status"]["state"] in ("completed", "failed"):
            break
        import time; time.sleep(0.02)

    assert out["status"]["state"] == "completed"
    assert len(out["artifacts"]) == 1
    assert "claude-sonnet-4-5" in out["artifacts"][0]["text"]


def test_fan_out_with_sub_prompts(client):
    resp = client.post(
        "/messages",
        json={
            "parts": [{"kind": "text", "text": "header prompt"}],
            "metadata": {
                "model": "gpt-4o",
                "sub_prompts": "research A||research B||research C||research D||research E",
                "concurrency": 3,
            },
        },
    )
    task_id = resp.json()["taskId"]

    for _ in range(50):
        out = client.get(f"/tasks/{task_id}").json()
        if out["status"]["state"] in ("completed", "failed"):
            break
        import time; time.sleep(0.02)

    assert out["status"]["state"] == "completed"
    assert len(out["artifacts"]) == 5
    assert out["result"]["failed_count"] == 0
    assert all("gpt-4o" in a["text"] for a in out["artifacts"])


def test_missing_text_part_returns_400(client):
    resp = client.post("/messages", json={"parts": [], "metadata": {}})
    assert resp.status_code == 400


def test_unknown_task_returns_404(client):
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code == 404
