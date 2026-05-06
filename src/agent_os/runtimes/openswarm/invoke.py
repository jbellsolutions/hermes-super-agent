"""openswarm runtime invoke entry point.

The runtime owns a fleet, so invoke() is a small dispatcher over fleet ops.
Builder ops (build/upgrade) are gated to Phase B and currently raise
NotImplementedError; routing surface is stable.
"""
from __future__ import annotations

import time
from typing import Any

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact

from . import builder, fleet


def _ok(job_id: str, output: Any, t0: float) -> RuntimeResult:
    return RuntimeResult(
        runtime="openswarm",
        job_id=job_id,
        status="ok",
        output=output,
        latency_ms=int((time.time() - t0) * 1000),
    )


def _err(job_id: str, message: str, t0: float) -> RuntimeResult:
    return RuntimeResult(
        runtime="openswarm",
        job_id=job_id,
        status="error",
        error=message,
        latency_ms=int((time.time() - t0) * 1000),
    )


def invoke(job: dict) -> RuntimeResult:
    """Dispatch a fleet operation.

    Job shape:
        op: "run" | "list" | "status" | "start" | "stop" | "restart" |
            "destroy" | "build" | "upgrade" | "cleanup" | "cost" |
            "hibernate" | "snapshot" | "pipeline" | "fan_out"
            (default: "run")
        swarm: str    (default: "default"; required for status/start/stop/...)
        agent: str    (default: "auto" — let OpenSwarm orchestrator route)
        prompt: str   (required for op=run)
        files: list[str]
        name: str           required for op=build
        description: str    required for op=build
        customizer: str     (default: "claude_code"; "manual" | "noop" | dict)
        customizer_options: dict | None
        validator: str      (default: "health"; "smoke" | "noop")
        cost_budget_daily_usd: float (default: 10.0)
        days: int           cost rollup window (default: 1)
        default_minutes: float | None  hibernate threshold override
        steps: list[dict]   pipeline step list
        prompts: list[str]  fan_out prompts
        concurrency: int    fan_out parallelism (default: 4)
    """
    t0 = time.time()
    job_id = new_job_id()
    op = job.get("op", "run")
    try:
        if op == "run":
            output: Any = fleet.run(
                swarm=job.get("swarm", "default"),
                agent=job.get("agent", "auto"),
                prompt=job["prompt"],
                files=job.get("files", []),
            )
        elif op == "list":
            output = fleet.list_swarms()
        elif op == "status":
            output = fleet.status(job.get("swarm"))
        elif op == "start":
            output = fleet.start(job["swarm"])
        elif op == "stop":
            output = fleet.stop(job["swarm"], kill=bool(job.get("kill", False)))
        elif op == "restart":
            output = fleet.restart(job["swarm"])
        elif op == "destroy":
            output = fleet.destroy(job["swarm"])
        elif op == "cleanup":
            output = fleet.cleanup_orphans()
        elif op == "cost":
            output = fleet.cost_rollup(
                swarm=job.get("swarm"),
                days=int(job.get("days", 1)),
            )
        elif op == "hibernate":
            output = fleet.hibernate_idle(default_minutes=job.get("default_minutes"))
        elif op == "snapshot":
            output = fleet.snapshot_json(write=bool(job.get("write", True)))
        elif op == "pipeline":
            output = fleet.pipeline(steps=job["steps"])
        elif op == "fan_out":
            output = fleet.fan_out(
                swarm=job["swarm"],
                prompts=job["prompts"],
                agent=job.get("agent", "auto"),
                concurrency=int(job.get("concurrency", 4)),
                files=job.get("files"),
            )
        elif op == "build":
            output = builder.build(
                name=job["name"],
                description=job["description"],
                customizer=job.get("customizer", "claude_code"),
                customizer_options=job.get("customizer_options"),
                validator=job.get("validator", "health"),
                cost_budget_daily_usd=float(job.get("cost_budget_daily_usd", 10.0)),
            )
        elif op == "upgrade":
            output = builder.upgrade(
                name=job["swarm"],
                validator=job.get("validator", "health"),
            )
        else:
            result = _err(job_id, f"unknown op: {op!r}", t0)
            write_run_artifact(result)
            return result
    except Exception as e:  # noqa: BLE001 — surface every failure cleanly
        result = _err(job_id, f"{type(e).__name__}: {e}", t0)
        write_run_artifact(result)
        return result

    result = _ok(job_id, output, t0)
    write_run_artifact(result)
    return result
