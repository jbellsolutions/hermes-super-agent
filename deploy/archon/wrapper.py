"""A2A wrapper around the Archon agent-builder.

Archon (https://github.com/coleam00/Archon) is a meta-agent that generates
complete agent specs (AGENT.md + skills + Railway config) from natural
language. This wrapper exposes Archon's `generate_agent` capability behind
the standard A2A protocol so Hermes Admiral can delegate "build a specialist"
jobs to it.

POST /messages with parts=[{"text": "create a LinkedIn outreach specialist"}]
→ Archon generates the spec
→ wrapper returns a task with artifacts=[{kind:"text", text:<AGENT.md>}, ...]

Deploy as a sidecar to your Archon container.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("archon-a2a")

app = FastAPI(title="Archon A2A Wrapper", version="0.1.0")

_PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:8001")
_ARCHON_BASE = os.getenv("ARCHON_BASE_URL", "http://localhost:8100")  # Archon's own UI/API


# ---------------------------------------------------------------------------
# In-memory task store
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_id: str
    prompt: str
    state: str = "submitted"
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


_tasks: dict[str, Task] = {}


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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/agentCard")
async def agent_card() -> dict:
    return {
        "name": "Archon Agent Builder",
        "description": "Meta-agent that generates AGENT.md + skill definitions + deploy config from a natural-language specialist spec.",
        "url": _PUBLIC_URL,
        "version": "0.1.0",
        "skills": [
            {
                "id": "build_specialist",
                "name": "Build a specialist",
                "description": "Generate a complete agent spec: AGENT.md, skill files, and Railway deploy config.",
                "tags": ["build-specialist", "archon", "agent-gen"],
                "examples": [
                    "Create a LinkedIn outreach specialist",
                    "Build a SOC2 audit reviewer specialist",
                ],
            }
        ],
    }


@app.post("/messages")
async def submit(req: MessageRequest):
    prompt = "\n".join(p.text for p in req.parts if p.kind == "text" and p.text)
    if not prompt:
        raise HTTPException(status_code=400, detail="No text part in message")

    task_id = req.taskId or str(uuid.uuid4())
    task = Task(task_id=task_id, prompt=prompt)
    _tasks[task_id] = task
    asyncio.create_task(_run(task_id))
    return {"taskId": task_id, "state": "submitted"}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "taskId": task.task_id,
        "status": {"state": task.state},
        "artifacts": task.artifacts,
        "result": {"error": task.error} if task.error else {},
    }


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

async def _run(task_id: str) -> None:
    task = _tasks.get(task_id)
    if task is None:
        return
    task.state = "working"
    try:
        artifacts = await _delegate_to_archon(task.prompt)
        task.artifacts = artifacts
        task.state = "completed"
    except Exception as exc:
        logger.exception("Archon delegation failed")
        task.error = str(exc)
        task.state = "failed"


async def _delegate_to_archon(prompt: str) -> list[dict[str, Any]]:
    """Hand the spec to Archon and collect generated files as artifacts.

    Replace this stub with the actual Archon SDK / API call once you wire
    your Archon deployment. The Hermes spawner only cares that artifacts
    contains an 'AGENT.md' text part — anything else is bonus.
    """
    import httpx
    archon_url = _ARCHON_BASE.rstrip("/")
    payload = {"prompt": prompt}

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f"{archon_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        # Stub mode: return a minimal AGENT.md so the spawner pipeline can be tested
        # end-to-end without a live Archon. Replace once Archon is wired.
        logger.warning("Archon unreachable (%s) — returning stub AGENT.md", exc)
        return [
            {
                "kind": "text",
                "name": "AGENT.md",
                "text": _stub_agent_md(prompt),
            }
        ]

    artifacts = []
    for fname, content in (data.get("files") or {}).items():
        artifacts.append({"kind": "text", "name": fname, "text": content})
    return artifacts


def _stub_agent_md(prompt: str) -> str:
    return f"""# Generated specialist (stub)

## Mission
{prompt}

## Model
claude-sonnet-4-5

## Tools
- hermes_self
- terminal

## Notes
This is a stub AGENT.md — wire Archon's /api/generate to replace this.
"""


def run() -> None:
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("wrapper:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run()
