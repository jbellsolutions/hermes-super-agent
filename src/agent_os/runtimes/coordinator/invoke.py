"""Fan-out coordinator runtime invocation.

The Coordinator is a deployed A2A service that internally fans a job out
across N parallel sub-agents. Admiral delegates fan-out tagged jobs to it
and watches NATS for progress; the coordinator handles the swarm.

The model the coordinator uses is selectable per-job:

    job.metadata['coordinator_model'] = 'claude-sonnet-4.7'

Falls back to COORDINATOR_DEFAULT_MODEL env var, then to whatever
the coordinator service has configured locally.

Two dispatch modes:

  Simple fan-out  → POST directly to /messages, poll /tasks/{id}.
  Durable fan-out → wrap in a Temporal FanOutWorkflow for crash recovery.
                    Used when sub_prompts is provided or estimated_minutes > 30.

Usage (from job_router.dispatch):
    from agent_os.runtimes.coordinator import invoke
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

_COORDINATOR_URL = os.getenv("COORDINATOR_URL", "")
_DEFAULT_MODEL = os.getenv("COORDINATOR_DEFAULT_MODEL", "")
_POLL_INTERVAL = 5
_POLL_TIMEOUT = 7200  # 2 hours

_NATS_SUBJECT_BASE = "agents.coordinator"


async def run(job: Job) -> dict[str, Any]:
    """Dispatch a fan-out job to the Coordinator service.

    Returns a result dict with status, elapsed_seconds, and any artifacts.
    """
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()
    model = _select_model(job)

    if not _COORDINATOR_URL:
        logger.warning("COORDINATOR_URL not set — using local asyncio fan-out fallback")
        return await _local_fallback(job, task_id, model)

    publish_event(f"{_NATS_SUBJECT_BASE}.task.started", {
        "task_id": task_id,
        "prompt": job.prompt[:200],
        "runtime": "coordinator",
        "model": model,
    })

    if _should_use_temporal(job):
        return await _temporal_dispatch(job, task_id, t0, model)
    return await _a2a_dispatch(job, task_id, t0, model)


def _select_model(job: Job) -> str:
    """Resolve which model the coordinator should use for this job.

    Priority: job.metadata['coordinator_model'] > env COORDINATOR_DEFAULT_MODEL > "".
    Empty string means: let the coordinator service use its own configured default.
    """
    return job.metadata.get("coordinator_model") or _DEFAULT_MODEL or ""


def _should_use_temporal(job: Job) -> bool:
    """Use Temporal for large fan-outs or long-running jobs."""
    if job.estimated_minutes and job.estimated_minutes > 30:
        return True
    if "sub_prompts" in job.metadata:
        return True
    return "temporal" in {tag.lower() for tag in job.tags}


async def _a2a_dispatch(job: Job, task_id: str, t0: float, model: str) -> dict[str, Any]:
    """POST to coordinator A2A endpoint and poll for completion."""
    metadata = {
        "tags": ",".join(job.tags),
        "runtime": "coordinator",
    }
    if model:
        metadata["model"] = model

    payload = {
        "parts": [{"kind": "text", "text": job.prompt}],
        "taskId": task_id,
        "metadata": metadata,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(f"{_COORDINATOR_URL}/messages", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Coordinator A2A submission failed: %s", exc)
            return _error_result(task_id, str(exc), t0)

        submitted = resp.json()
        remote_task_id = submitted.get("taskId", task_id)

        elapsed = 0.0
        while elapsed < _POLL_TIMEOUT:
            await asyncio.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL

            try:
                status_resp = await client.get(f"{_COORDINATOR_URL}/tasks/{remote_task_id}")
                status_resp.raise_for_status()
                task_data = status_resp.json()
            except httpx.HTTPError:
                continue

            state = task_data.get("status", {}).get("state", "unknown")

            if state == "completed":
                publish_event(f"{_NATS_SUBJECT_BASE}.task.completed", {
                    "task_id": task_id,
                    "elapsed_seconds": time.monotonic() - t0,
                })
                return {
                    "status": "completed",
                    "task_id": task_id,
                    "elapsed_seconds": time.monotonic() - t0,
                    "model": model,
                    "artifacts": task_data.get("artifacts", []),
                    "result": task_data.get("result"),
                }

            if state in ("failed", "cancelled"):
                error = task_data.get("result", {}).get("error", "unknown error")
                publish_event(f"{_NATS_SUBJECT_BASE}.task.failed", {
                    "task_id": task_id,
                    "error": error,
                })
                return _error_result(task_id, error, t0)

            publish_event(f"{_NATS_SUBJECT_BASE}.task.progress", {
                "task_id": task_id,
                "state": state,
                "elapsed_seconds": elapsed,
            })

    return _error_result(task_id, f"timeout after {_POLL_TIMEOUT}s", t0)


async def _temporal_dispatch(job: Job, task_id: str, t0: float, model: str) -> dict[str, Any]:
    """Wrap the fan-out in a Temporal durable workflow."""
    from agent_os.workflows.fan_out import FanOutJob, run_fan_out_workflow

    sub_prompts_raw = job.metadata.get("sub_prompts", "")
    sub_prompts = [
        p.strip() for p in sub_prompts_raw.split("||") if p.strip()
    ] if sub_prompts_raw else []

    fan_out_job = FanOutJob(
        task_id=task_id,
        prompt=job.prompt,
        sub_prompts=sub_prompts,
        engine="coordinator",
        model=model,
        concurrency=min(300, len(sub_prompts) or 50),
        agent_id="admiral",
    )

    result = await run_fan_out_workflow(fan_out_job)

    publish_event(f"{_NATS_SUBJECT_BASE}.task.completed", {
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "failed_count": result.failed_count,
    })

    return {
        "status": "completed" if result.failed_count == 0 else "partial",
        "task_id": task_id,
        "elapsed_seconds": result.elapsed_seconds,
        "model": model,
        "results": result.results,
        "failed_count": result.failed_count,
    }


async def _local_fallback(job: Job, task_id: str, model: str) -> dict[str, Any]:
    """Development fallback — stubs cleanly when COORDINATOR_URL unset."""
    return {
        "status": "completed",
        "task_id": task_id,
        "elapsed_seconds": 0.0,
        "model": model,
        "note": "local fallback — COORDINATOR_URL not set",
        "prompt": job.prompt,
    }


def _error_result(task_id: str, error: str, t0: float) -> dict[str, Any]:
    return {
        "status": "error",
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "error": error,
    }
