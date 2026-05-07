"""Temporal durable workflow — wraps fan-out operations for crash recovery.

When a 300-agent Kimi fan-out is 200 steps in and the Admiral's VPS reboots,
Temporal resumes exactly where it stopped. No "did the fan-out complete?"
uncertainty.

The workflow has two dispatch paths:
  1. Kimi K2.6 Coordinator — preferred for true parallel fan-out (up to 300 sub-agents)
  2. OpenSwarm fleet.fan_out — for local swarm fan-out (existing 14 runtimes)

Usage:
    from temporalio.client import Client
    from agent_os.workflows.fan_out import FanOutWorkflow, FanOutJob

    client = await Client.connect("temporal-host:7233")
    result = await client.execute_workflow(
        FanOutWorkflow.run,
        FanOutJob(
            task_id="abc123",
            prompt="Research 200 AI startups",
            sub_prompts=["Research company A", "Research company B", ...],
            engine="kimi",
            concurrency=300,
        ),
        id="fan-out-abc123",
        task_queue="hermes-fleet",
    )
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FanOutJob:
    task_id: str
    prompt: str
    sub_prompts: list[str] = field(default_factory=list)
    engine: str = "kimi"            # "kimi" | "openswarm"
    concurrency: int = 50
    agent_id: str = "admiral"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FanOutResult:
    task_id: str
    results: list[dict[str, Any]] = field(default_factory=list)
    failed_count: int = 0
    engine: str = "kimi"
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Temporal workflow + activities
# (Temporal import is lazy so the rest of agent_os works without temporalio)
# ---------------------------------------------------------------------------

def _temporal_available() -> bool:
    try:
        import temporalio  # noqa: F401
        return True
    except ImportError:
        return False


async def run_fan_out_workflow(job: FanOutJob) -> FanOutResult:
    """Entry point — uses Temporal if available, falls back to asyncio gather."""
    if not _temporal_available():
        logger.warning("temporalio not installed — running fan-out without durability")
        return await _asyncio_fan_out(job)

    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")

    try:
        from temporalio.client import Client
        client = await Client.connect(temporal_host)
        result = await client.execute_workflow(
            FanOutWorkflow.run,
            job,
            id=f"fan-out-{job.task_id}",
            task_queue="hermes-fleet",
            execution_timeout=timedelta(hours=4),
        )
        return result
    except Exception as exc:
        logger.warning("Temporal unavailable (%s) — falling back to asyncio fan-out", exc)
        return await _asyncio_fan_out(job)


async def _asyncio_fan_out(job: FanOutJob) -> FanOutResult:
    """Best-effort asyncio gather — used when Temporal is unreachable."""
    import time
    t0 = time.monotonic()

    sem = asyncio.Semaphore(job.concurrency)

    async def _run_one(sub_prompt: str) -> dict[str, Any]:
        async with sem:
            return await _delegate_to_agent_activity({"task_id": job.task_id, "prompt": sub_prompt, "engine": job.engine})

    tasks = [_run_one(p) for p in job.sub_prompts]
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    failed = 0
    for r in raw:
        if isinstance(r, Exception):
            failed += 1
            results.append({"error": str(r)})
        else:
            results.append(r)

    return FanOutResult(
        task_id=job.task_id,
        results=results,
        failed_count=failed,
        engine=job.engine,
        elapsed_seconds=time.monotonic() - t0,
    )


# ---------------------------------------------------------------------------
# Temporal workflow definition (only imported by Temporal workers)
# ---------------------------------------------------------------------------

try:
    from temporalio import activity, workflow
    from temporalio.common import RetryPolicy

    @activity.defn
    async def decompose_job_activity(job: FanOutJob) -> list[str]:
        """Split a high-level job into sub-prompts if none provided."""
        if job.sub_prompts:
            return job.sub_prompts
        # Minimal decomposition — callers should pre-fill sub_prompts
        return [job.prompt]

    @activity.defn
    async def delegate_to_agent_activity(sub_task: dict[str, Any]) -> dict[str, Any]:
        return await _delegate_to_agent_activity(sub_task)

    @activity.defn
    async def aggregate_results_activity(results: list[dict[str, Any]]) -> FanOutResult:
        task_id = results[0].get("task_id", "unknown") if results else "unknown"
        failed = sum(1 for r in results if "error" in r)
        return FanOutResult(task_id=task_id, results=results, failed_count=failed)

    @workflow.defn
    class FanOutWorkflow:
        """Durable fan-out: decompose → parallel delegate → aggregate.

        Survives worker restarts — Temporal replays from the last successful
        activity checkpoint. No activity is re-executed after success.
        """

        @workflow.run
        async def run(self, job: FanOutJob) -> FanOutResult:
            retry = RetryPolicy(maximum_attempts=3, backoff_coefficient=2.0)

            # Step 1 — decompose
            sub_prompts = await workflow.execute_activity(
                decompose_job_activity,
                job,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry,
            )

            # Step 2 — fan out in parallel (Temporal caps concurrency via semaphore)
            sem = asyncio.Semaphore(job.concurrency)

            async def _one(prompt: str) -> dict[str, Any]:
                async with sem:
                    return await workflow.execute_activity(
                        delegate_to_agent_activity,
                        {"task_id": job.task_id, "prompt": prompt, "engine": job.engine},
                        start_to_close_timeout=timedelta(hours=2),
                        retry_policy=retry,
                    )

            results = await asyncio.gather(*[_one(p) for p in sub_prompts])

            # Step 3 — aggregate
            return await workflow.execute_activity(
                aggregate_results_activity,
                list(results),
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry,
            )

except ImportError:
    # temporalio not installed — define stub so imports don't break
    class FanOutWorkflow:  # type: ignore[no-redef]
        @staticmethod
        async def run(job: FanOutJob) -> FanOutResult:
            return await _asyncio_fan_out(job)


# ---------------------------------------------------------------------------
# Shared activity implementation (used by both Temporal and asyncio paths)
# ---------------------------------------------------------------------------

async def _delegate_to_agent_activity(sub_task: dict[str, Any]) -> dict[str, Any]:
    """Route a single sub-task to the appropriate engine."""
    engine = sub_task.get("engine", "kimi")
    prompt = sub_task.get("prompt", "")
    task_id = sub_task.get("task_id", "unknown")

    if engine == "kimi":
        return await _run_kimi_subtask(task_id, prompt)
    elif engine == "openswarm":
        return await _run_openswarm_subtask(task_id, prompt)
    else:
        return {"task_id": task_id, "prompt": prompt, "status": "skipped", "reason": f"unknown engine: {engine}"}


async def _run_kimi_subtask(task_id: str, prompt: str) -> dict[str, Any]:
    """Delegate to the Kimi K2.6 Coordinator via A2A."""
    kimi_url = os.getenv("KIMI_COORDINATOR_URL", "")
    if not kimi_url:
        return {"task_id": task_id, "status": "error", "error": "KIMI_COORDINATOR_URL not set"}

    import httpx
    payload = {
        "parts": [{"kind": "text", "text": prompt}],
        "taskId": f"{task_id}-kimi",
        "metadata": {"engine": "kimi"},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{kimi_url}/messages", json=payload)
            resp.raise_for_status()
            return {"task_id": task_id, "status": "delegated", "kimi_response": resp.json()}
    except Exception as exc:
        return {"task_id": task_id, "status": "error", "error": str(exc)}


async def _run_openswarm_subtask(task_id: str, prompt: str) -> dict[str, Any]:
    """Delegate a sub-task to the OpenSwarm fleet."""
    try:
        from agent_os.runtimes.openswarm import fleet
        result = fleet.fan_out(
            swarm="default",
            prompts=[prompt],
            agent="auto",
            concurrency=1,
        )
        return {"task_id": task_id, "status": "completed", "result": result}
    except Exception as exc:
        return {"task_id": task_id, "status": "error", "error": str(exc)}
