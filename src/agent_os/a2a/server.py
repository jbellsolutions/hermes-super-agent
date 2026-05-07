"""A2A HTTP server — the three routes every A2A-compliant agent must expose.

  GET  /agentCard         → Agent Card JSON
  POST /messages          → receive an inbound task delegation
  GET  /tasks/{task_id}   → poll task status

Task lifecycle: SUBMITTED → WORKING → COMPLETED | FAILED | CANCELLED

The server runs alongside Hermes as a FastAPI sub-application. It wires into
the existing orchestration stack:
  - Tier classifier gates every inbound delegation
  - Plan card content flows into the task response body
  - NATS publisher emits task.started / task.completed events

Run standalone for testing:
    uvicorn agent_os.a2a.server:app --port 8080 --reload
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Task store — in-memory for now; swap for Redis/SQLite for multi-instance
# ---------------------------------------------------------------------------

_tasks: dict[str, "A2ATask"] = {}


class TaskStatus(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class A2ATask:
    def __init__(self, task_id: str, message: dict[str, Any]) -> None:
        self.task_id = task_id
        self.message = message
        self.status = TaskStatus.SUBMITTED
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.result: dict[str, Any] | None = None
        self.artifacts: list[dict[str, Any]] = []
        self.plan_card: str | None = None  # rendered markdown plan card

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.task_id,
            "status": {"state": self.status.value},
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "message": self.message,
            "planCard": self.plan_card,
            "artifacts": self.artifacts,
            "result": self.result,
        }

    def set_status(self, status: TaskStatus, result: dict[str, Any] | None = None) -> None:
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if result:
            self.result = result


# ---------------------------------------------------------------------------
# FastAPI app factory
# ---------------------------------------------------------------------------

def create_a2a_app(agent_id: str | None = None, base_url: str | None = None):  # type: ignore[return]
    """Return a FastAPI app with the three A2A routes wired up.

    Import lazily so the rest of agent_os works without fastapi installed.
    """
    try:
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.responses import JSONResponse
    except ImportError:
        logger.error("fastapi not installed — A2A server unavailable. Run: uv add fastapi uvicorn")
        return None

    from agent_os.a2a.agent_card import build_card
    from agent_os.bus.nats_publisher import publish_event

    _agent_id = agent_id or os.getenv("HERMES_AGENT_ID", "admiral")
    _card = build_card(agent_id=_agent_id, base_url=base_url)

    app = FastAPI(title=f"A2A — {_agent_id}", version="1.0.0")

    # ------------------------------------------------------------------
    # GET /agentCard
    # ------------------------------------------------------------------

    @app.get("/agentCard")
    async def get_agent_card() -> JSONResponse:
        return JSONResponse(_card.to_dict())

    # ------------------------------------------------------------------
    # POST /messages  — receive inbound task delegation
    # ------------------------------------------------------------------

    @app.post("/messages")
    async def receive_message(request: Request) -> JSONResponse:
        body = await request.json()

        # A2A spec: message has a "parts" list with text content
        parts = body.get("parts", [])
        text_parts = [p.get("text", "") for p in parts if p.get("kind") == "text"]
        prompt = " ".join(text_parts).strip() or body.get("text", "")

        task_id = body.get("taskId") or str(uuid.uuid4())
        task = A2ATask(task_id=task_id, message=body)
        _tasks[task_id] = task

        # Emit NATS event
        publish_event(f"agents.{_agent_id}.task.started", {
            "task_id": task_id,
            "prompt": prompt[:200],
            "source": "a2a",
        })

        # Dispatch asynchronously via orchestration stack
        asyncio.create_task(_dispatch_task(task, prompt, _agent_id))

        return JSONResponse({"taskId": task_id, "status": "submitted"}, status_code=202)

    # ------------------------------------------------------------------
    # GET /tasks/{task_id}
    # ------------------------------------------------------------------

    @app.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> JSONResponse:
        task = _tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return JSONResponse(task.to_dict())

    # ------------------------------------------------------------------
    # Health (Railway healthcheck target)
    # ------------------------------------------------------------------

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "agent": _agent_id})

    return app


# ---------------------------------------------------------------------------
# Task dispatcher — wires into the Phase F orchestration stack
# ---------------------------------------------------------------------------

async def _dispatch_task(task: A2ATask, prompt: str, agent_id: str) -> None:
    """Run the orchestration pipeline for an inbound A2A task."""
    from agent_os.bus.nats_publisher import publish_event

    task.set_status(TaskStatus.WORKING)

    try:
        # Build a Job and run through the Phase F planner stack
        from agent_os.orchestrator.adapters.job_router import Job, route
        from agent_os.orchestrator.tool_planner import plan
        from agent_os.orchestrator.plan_card import render_markdown

        tags = set(task.message.get("metadata", {}).get("tags", "").split(","))
        tags.discard("")

        job = Job(prompt=prompt, tags=tags)
        tool_plan = plan(job)
        plan_card_md = render_markdown(tool_plan)

        task.plan_card = plan_card_md
        runtime = route(job)

        task.set_status(TaskStatus.COMPLETED, result={
            "runtime": runtime,
            "planCard": plan_card_md,
            "tier": tool_plan.tier,
            "model": tool_plan.model_recommendation,
        })
        task.artifacts.append({
            "type": "text/markdown",
            "content": plan_card_md,
            "title": "Plan Card",
        })

        publish_event(f"agents.{agent_id}.task.completed", {
            "task_id": task.task_id,
            "runtime": runtime,
            "tier": tool_plan.tier,
        })

    except Exception as exc:
        logger.exception("A2A task dispatch failed for %s", task.task_id)
        task.set_status(TaskStatus.FAILED, result={"error": str(exc)})
        publish_event(f"agents.{agent_id}.task.failed", {
            "task_id": task.task_id,
            "error": str(exc),
        })


# ---------------------------------------------------------------------------
# Standalone entrypoint for development
# ---------------------------------------------------------------------------

app = create_a2a_app()
