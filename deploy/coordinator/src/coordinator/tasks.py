"""Task state + fan-out execution.

A submitted task lives in memory while it runs. We track:
  state:    submitted | working | completed | failed
  results:  list[dict] — one entry per sub-prompt
  failed:   int — how many sub-prompts errored

Fan-out logic:
  - If metadata['sub_prompts'] is provided (||-separated string or list),
    each becomes a parallel LLM call.
  - Else: single LLM call, no fan-out.

Concurrency capped via metadata['concurrency'] or env COORDINATOR_MAX_CONCURRENCY (default 50).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from .llm import call_llm
from .nats_pub import publish

logger = logging.getLogger(__name__)

_DEFAULT_CONCURRENCY = int(os.getenv("COORDINATOR_MAX_CONCURRENCY", "50"))

# Hard ceiling on sub-prompts per fan-out. A confused or hostile request like
# `sub_prompts=("research X" * 10000)` would otherwise blow your LLM budget
# and rate limits. Override via COORDINATOR_MAX_SUBTASKS for power users.
_MAX_SUBTASKS = int(os.getenv("COORDINATOR_MAX_SUBTASKS", "300"))


class TooManySubtasks(ValueError):
    pass


@dataclass
class Task:
    task_id: str
    prompt: str
    model: str
    metadata: dict[str, Any]
    state: str = "submitted"
    results: list[dict[str, Any]] = field(default_factory=list)
    failed_count: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def create(self, prompt: str, model: str, metadata: dict[str, Any], task_id: str | None = None) -> Task:
        async with self._lock:
            tid = task_id or str(uuid.uuid4())
            task = Task(task_id=tid, prompt=prompt, model=model, metadata=metadata)
            self._tasks[tid] = task
            return task

    async def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    async def update_state(self, task_id: str, state: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.state = state
            if state in ("completed", "failed"):
                task.completed_at = time.time()


_store = TaskStore()


def get_store() -> TaskStore:
    return _store


async def run_task(task_id: str) -> None:
    """Drive a task to completion. Spawned via asyncio.create_task; never awaited directly."""
    task = await _store.get(task_id)
    if task is None:
        return

    await _store.update_state(task_id, "working")
    await publish(
        f"agents.coordinator.task.{task_id}.started",
        {"task_id": task_id, "model": task.model, "prompt": task.prompt[:200]},
    )

    try:
        sub_prompts = _resolve_sub_prompts(task)
        if len(sub_prompts) > _MAX_SUBTASKS:
            raise TooManySubtasks(
                f"{len(sub_prompts)} sub-prompts exceeds COORDINATOR_MAX_SUBTASKS={_MAX_SUBTASKS}. "
                f"Lower the count or raise the env limit if you mean it."
            )
        # Cap concurrency at min(metadata, default, total subtasks). No point
        # spawning 50 workers for 5 sub-prompts, and no point letting metadata
        # request 1000 concurrent calls (would hit rate limits).
        requested_conc = int(task.metadata.get("concurrency") or _DEFAULT_CONCURRENCY)
        concurrency = max(1, min(requested_conc, _DEFAULT_CONCURRENCY, len(sub_prompts)))
        sem = asyncio.Semaphore(concurrency)

        async def _one(idx: int, sub: str) -> dict[str, Any]:
            async with sem:
                t0 = time.time()
                try:
                    result = await call_llm(task.model, sub)
                    out = {
                        "index": idx,
                        "status": "completed",
                        "text": result.text,
                        "input_tokens": result.input_tokens,
                        "output_tokens": result.output_tokens,
                        "elapsed_seconds": time.time() - t0,
                    }
                except Exception as exc:
                    logger.warning("sub-task %d failed: %s", idx, exc)
                    out = {
                        "index": idx,
                        "status": "error",
                        "error": str(exc),
                        "elapsed_seconds": time.time() - t0,
                    }
                # Fire a per-subtask progress event.
                await publish(
                    f"agents.coordinator.task.{task_id}.progress",
                    {"task_id": task_id, "index": idx, "status": out["status"]},
                )
                return out

        results = await asyncio.gather(*[_one(i, p) for i, p in enumerate(sub_prompts)])
        task.results = results
        task.failed_count = sum(1 for r in results if r["status"] != "completed")
        await _store.update_state(task_id, "completed")
        await publish(
            f"agents.coordinator.task.{task_id}.completed",
            {
                "task_id": task_id,
                "model": task.model,
                "subtask_count": len(results),
                "failed_count": task.failed_count,
                "elapsed_seconds": time.time() - task.started_at,
            },
        )
    except Exception as exc:
        logger.exception("task %s failed", task_id)
        task.error = str(exc)
        await _store.update_state(task_id, "failed")
        await publish(
            f"agents.coordinator.task.{task_id}.failed",
            {"task_id": task_id, "error": str(exc)},
        )


def _resolve_sub_prompts(task: Task) -> list[str]:
    raw = task.metadata.get("sub_prompts")
    if isinstance(raw, list):
        return [str(p).strip() for p in raw if str(p).strip()]
    if isinstance(raw, str) and raw:
        return [p.strip() for p in raw.split("||") if p.strip()]
    return [task.prompt]
