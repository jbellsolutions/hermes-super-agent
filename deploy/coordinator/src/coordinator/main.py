"""Hermes Coordinator — A2A-compliant fan-out service.

Three HTTP routes (A2A protocol):
  GET  /agentCard         → service description
  POST /messages          → submit a job, return taskId
  GET  /tasks/{task_id}   → task state + results

Plus:
  GET  /health            → Railway/uptime ping

Run locally:
  uv run hermes-coordinator
or:
  uv run uvicorn coordinator.main:app --host 0.0.0.0 --port 8000

Deploy:
  railway up
"""
from __future__ import annotations

import asyncio
import logging
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .tasks import get_store, run_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Hermes Coordinator", version="0.1.0")

_PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Part(BaseModel):
    kind: str = "text"
    text: str = ""


class MessageRequest(BaseModel):
    parts: list[Part] = Field(default_factory=list)
    taskId: str | None = None
    metadata: dict = Field(default_factory=dict)


class MessageResponse(BaseModel):
    taskId: str
    state: str = "submitted"


class TaskStatus(BaseModel):
    taskId: str
    state: str
    artifacts: list = Field(default_factory=list)
    result: dict | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/agentCard")
async def agent_card() -> dict:
    return {
        "name": "Hermes Coordinator",
        "description": "Fan-out coordinator. Decomposes a job into N parallel sub-tasks and runs each on the model specified per-job. Backed by Anthropic / OpenAI / DeepSeek / Moonshot / OpenRouter.",
        "url": _PUBLIC_URL,
        "version": "0.1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "fan_out",
                "name": "Parallel fan-out",
                "description": "Run N independent sub-prompts in parallel on a chosen model.",
                "tags": ["fan-out", "swarm-coordinator", "parallel", "batch"],
                "examples": [
                    "Research these 50 companies in parallel",
                    "Categorize these 300 support tickets",
                ],
            }
        ],
    }


@app.post("/messages")
async def submit(req: MessageRequest) -> MessageResponse:
    prompt = "\n".join(p.text for p in req.parts if p.kind == "text" and p.text)
    if not prompt:
        raise HTTPException(status_code=400, detail="No text part in message")

    # Honor planner's model_recommendation alongside the explicit `model` field.
    model = str(
        req.metadata.get("model")
        or req.metadata.get("model_recommendation")
        or os.getenv("COORDINATOR_DEFAULT_MODEL", "")
    )
    store = get_store()
    task = await store.create(prompt=prompt, model=model, metadata=req.metadata, task_id=req.taskId)
    asyncio.create_task(run_task(task.task_id))
    return MessageResponse(taskId=task.task_id, state="submitted")


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    store = get_store()
    task = await store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    artifacts = []
    if task.state == "completed":
        artifacts = [
            {"index": r["index"], "kind": "text", "text": r.get("text", ""), "status": r["status"]}
            for r in task.results
        ]

    return {
        "taskId": task.task_id,
        "status": {"state": task.state},
        "artifacts": artifacts,
        "result": {
            "model": task.model,
            "subtask_count": len(task.results),
            "failed_count": task.failed_count,
            "error": task.error,
        },
    }


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run() -> None:
    """Console entry — `uv run hermes-coordinator`."""
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("coordinator.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run()
