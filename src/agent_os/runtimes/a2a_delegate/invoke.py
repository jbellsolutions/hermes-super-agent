"""A2A delegate runtime — routes job to an external A2A agent endpoint.

Invoked by dispatch() when job_router returns 'a2a_delegate'.
Covers: Archon agent builder (build-specialist tag), generic A2A targets.

The target A2A endpoint is resolved from:
  1. job.metadata['a2a_endpoint']  — explicit override
  2. job.metadata['agent_id']      — look up in vault/projects/registry.yaml
  3. ARCHON_A2A_URL env var        — default for build-specialist jobs
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any

import httpx

from agent_os.orchestrator.adapters.job_router import Job
from agent_os.bus.nats_publisher import publish_event

logger = logging.getLogger(__name__)

_ARCHON_URL = os.getenv("ARCHON_A2A_URL", "")
_POLL_INTERVAL = 5
_POLL_TIMEOUT = 600  # 10 minutes


async def run(job: Job) -> dict[str, Any]:
    """Delegate job to an external A2A endpoint."""
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()

    endpoint = _resolve_endpoint(job)
    if not endpoint:
        logger.warning("No A2A endpoint resolved for job — returning stub")
        return {
            "status": "stub",
            "task_id": task_id,
            "note": "No A2A endpoint configured. Set ARCHON_A2A_URL or job.metadata['a2a_endpoint'].",
            "elapsed_seconds": time.monotonic() - t0,
        }

    publish_event("agents.admiral.task.started", {
        "task_id": task_id,
        "runtime": "a2a_delegate",
        "endpoint": endpoint,
        "prompt": job.prompt[:200],
    })

    payload = {
        "jsonrpc": "2.0",
        "id": task_id,
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": job.prompt}],
            },
            "metadata": dict(job.metadata),
        },
    }

    messages_url = endpoint.rstrip("/") + "/messages"
    tasks_url = endpoint.rstrip("/") + "/tasks"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(messages_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            remote_task_id = (data.get("result") or {}).get("id", task_id)

        # Poll for completion
        result = await _poll_task(tasks_url, remote_task_id)

    except httpx.HTTPError as exc:
        logger.error("A2A delegate to %s failed: %s", endpoint, exc)
        publish_event("agents.admiral.task.failed", {"task_id": task_id, "error": str(exc)})
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(exc),
            "elapsed_seconds": time.monotonic() - t0,
        }

    publish_event("agents.admiral.task.completed", {
        "task_id": task_id,
        "runtime": "a2a_delegate",
        "elapsed_seconds": time.monotonic() - t0,
    })
    return {
        "status": result.get("status", "completed"),
        "task_id": task_id,
        "result": result,
        "elapsed_seconds": time.monotonic() - t0,
    }


def _resolve_endpoint(job: Job) -> str:
    if job.metadata.get("a2a_endpoint"):
        return job.metadata["a2a_endpoint"]

    tags = {t.lower() for t in job.tags}
    if "build-specialist" in tags or "archon" in tags:
        return _ARCHON_URL

    agent_id = job.metadata.get("agent_id", "")
    if agent_id:
        return _lookup_registry(agent_id)

    return ""


def _lookup_registry(agent_id: str) -> str:
    """Look up a2a_endpoint for agent_id in vault/projects/registry.yaml."""
    import os
    from pathlib import Path
    try:
        import yaml
        registry_path = Path(os.environ.get("VAULT_ROOT", "./vault")) / "projects" / "registry.yaml"
        data = yaml.safe_load(registry_path.read_text())
        for agent in (data or {}).get("agents", []):
            if agent.get("id") == agent_id:
                return agent.get("a2a_endpoint", "")
    except Exception as exc:
        logger.warning("registry.yaml lookup failed: %s", exc)
    return ""


async def _poll_task(tasks_url: str, task_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + _POLL_TIMEOUT
    async with httpx.AsyncClient(timeout=10) as client:
        while time.monotonic() < deadline:
            try:
                resp = await client.get(f"{tasks_url}/{task_id}")
                resp.raise_for_status()
                data = resp.json()
                state = (data.get("result") or {}).get("status", {})
                if isinstance(state, dict):
                    state_str = state.get("state", "")
                else:
                    state_str = str(state)
                if state_str in ("completed", "failed", "canceled"):
                    return data.get("result", {})
            except httpx.HTTPError:
                pass
            await asyncio.sleep(_POLL_INTERVAL)
    return {"status": "timeout", "task_id": task_id}
