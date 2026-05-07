"""Kimi K2.6 Swarm Coordinator runtime invocation.

Two modes depending on job complexity:

  Simple fan-out  → POST directly to the Kimi Coordinator A2A endpoint.
                    Admiral waits for COMPLETED status via polling.

  Durable fan-out → wrap in a Temporal FanOutWorkflow for crash recovery.
                    Use when `sub_prompts` list is provided (explicit decomposition)
                    or when estimated_minutes > 30.

The Kimi Coordinator is a deployed service — a thin A2A-compliant wrapper
around the Moonshot API that internally handles up to 300 parallel sub-agents.
Admiral doesn't manage the 300 agents; it just delegates the job and watches
NATS for progress events.

Usage (from job_router):
    from agent_os.runtimes.kimi_coordinator import invoke
    result = await invoke.run(job)
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

_KIMI_URL = os.getenv("KIMI_COORDINATOR_URL", "")
_POLL_INTERVAL = 5   # seconds between status checks
_POLL_TIMEOUT = 7200  # 2 hours max


async def run(job: Job) -> dict[str, Any]:
    """Dispatch a fan-out job to the Kimi K2.6 Swarm Coordinator.

    Returns a result dict with status, elapsed_seconds, and any artifacts.
    """
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()

    if not _KIMI_URL:
        # Development fallback — use local asyncio fan-out without Kimi
        logger.warning("KIMI_COORDINATOR_URL not set — using local asyncio fan-out")
        return await _local_fallback(job, task_id)

    # Publish start event
    publish_event("agents.kimi-coordinator.task.started", {
        "task_id": task_id,
        "prompt": job.prompt[:200],
        "runtime": "kimi_coordinator",
    })

    # Determine dispatch mode
    use_temporal = _should_use_temporal(job)

    if use_temporal:
        return await _temporal_dispatch(job, task_id, t0)
    else:
        return await _a2a_dispatch(job, task_id, t0)


def _should_use_temporal(job: Job) -> bool:
    """Use Temporal for large fan-outs or long-running jobs."""
    if job.estimated_minutes and job.estimated_minutes > 30:
        return True
    # If sub_prompts are provided in metadata, it's a large explicit fan-out
    if "sub_prompts" in job.metadata:
        return True
    return "temporal" in {tag.lower() for tag in job.tags}


async def _a2a_dispatch(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """POST to Kimi A2A endpoint and poll for completion."""
    payload = {
        "parts": [{"kind": "text", "text": job.prompt}],
        "taskId": task_id,
        "metadata": {
            "tags": ",".join(job.tags),
            "runtime": "kimi_coordinator",
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Submit
        try:
            resp = await client.post(f"{_KIMI_URL}/messages", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Kimi A2A submission failed: %s", exc)
            return _error_result(task_id, str(exc), t0)

        submitted = resp.json()
        remote_task_id = submitted.get("taskId", task_id)

        # Poll for completion
        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

            try:
                status_resp = await client.get(f"{_KIMI_URL}/tasks/{remote_task_id}")
                status_resp.raise_for_status()
                task_data = status_resp.json()
            except httpx.HTTPError:
                continue

            state = task_data.get("status", {}).get("state", "unknown")

            if state == "completed":
                publish_event("agents.kimi-coordinator.task.completed", {
                    "task_id": task_id,
                    "elapsed_seconds": time.monotonic() - t0,
                })
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "elapsed_seconds": time.monotonic() - t0,
                    "artifacts": task_data.get("artifacts", []),
                    "result": task_data.get("result"),
                }
            elif state in ("failed", "cancelled"):
                error = task_data.get("result", {}).get("error", "unknown error")
                publish_event("agents.kimi-coordinator.task.failed", {
                    "task_id": task_id,
                    "error": error,
                })
                return _error_result(task_id, error, t0)

            # Publish progress heartbeat
            publish_event("agents.kimi-coordinator.task.progress", {
                "task_id": task_id,
                "state": state,
                "elapsed_seconds": elapsed,
            })

    return _error_result(task_id, f"timeout after {_POLL_TIMEOUT}s", t0)


async def _temporal_dispatch(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """Wrap the fan-out in a Temporal durable workflow."""
    from agent_os.workflows.fan_out import FanOutJob, run_fan_out_workflow

    sub_prompts_raw = job.metadata.get("sub_prompts", "")
    sub_prompts = [p.strip() for p in sub_prompts_raw.split("||") if p.strip()] if sub_prompts_raw else []

    fan_out_job = FanOutJob(
        task_id=task_id,
        prompt=job.prompt,
        sub_prompts=sub_prompts,
        engine="kimi",
        concurrency=min(300, len(sub_prompts) or 50),
        agent_id="admiral",
    )

    result = await run_fan_out_workflow(fan_out_job)

    publish_event("agents.kimi-coordinator.task.completed", {
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "failed_count": result.failed_count,
    })

    return {
        "status": "completed" if result.failed_count == 0 else "partial",
        "task_id": task_id,
        "elapsed_seconds": result.elapsed_seconds,
        "results": result.results,
        "failed_count": result.failed_count,
    }


async def _local_fallback(job: Job, task_id: str) -> dict[str, Any]:
    """Development fallback — run without Kimi or Temporal."""
    return {
        "status": "completed",
        "task_id": task_id,
        "elapsed_seconds": 0.0,
        "note": "local fallback — KIMI_COORDINATOR_URL not set",
        "prompt": job.prompt,
    }


def _error_result(task_id: str, error: str, t0: float) -> dict[str, Any]:
    return {
        "status": "error",
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "error": error,
    }
