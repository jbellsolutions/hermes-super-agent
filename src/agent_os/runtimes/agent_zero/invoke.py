"""Agent Zero runtime invoke — A2A wrapper around the Agent Zero host bridge.

Agent Zero handles browser-heavy and visual/autonomous-UI tasks. The local
stack runs at AGENT_ZERO_URL (default: http://127.0.0.1:5080). Admiral
delegates `browser-heavy` / `visual` / `autonomous-ui` tagged jobs here
via A2A and watches NATS for progress.

The dispatch path is sync (`invoke(job)`) to match the rest of the legacy
runtimes; under the hood it calls a thin httpx-based A2A client.
"""
from __future__ import annotations

import logging
import os
import time
import uuid

import httpx

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact

logger = logging.getLogger(__name__)

_AGENT_ZERO_URL = os.getenv("AGENT_ZERO_URL", "http://127.0.0.1:5080")
_TIMEOUT = int(os.getenv("AGENT_ZERO_TIMEOUT", "1800"))  # 30 min default


def invoke(job) -> RuntimeResult:
    """Delegate a browser/visual job to the local Agent Zero instance."""
    t0 = time.time()
    job_id = new_job_id()

    if not _AGENT_ZERO_URL:
        return _stub_result(job_id, t0, "AGENT_ZERO_URL unset")

    try:
        prompt = getattr(job, "prompt", None) or (job.get("prompt") if isinstance(job, dict) else "")
    except Exception:
        prompt = ""

    payload = {
        "parts": [{"kind": "text", "text": prompt}],
        "taskId": str(uuid.uuid4()),
    }

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(f"{_AGENT_ZERO_URL.rstrip('/')}/messages", json=payload)
            resp.raise_for_status()
            body = resp.json()
        result = RuntimeResult(
            runtime="agent_zero",
            job_id=job_id,
            status=body.get("status", "completed"),
            output=body,
            latency_ms=int((time.time() - t0) * 1000),
        )
    except httpx.HTTPError as exc:
        logger.warning("Agent Zero unreachable at %s: %s", _AGENT_ZERO_URL, exc)
        return _stub_result(job_id, t0, f"agent zero unreachable: {exc}")

    write_run_artifact(result)
    return result


def _stub_result(job_id: str, t0: float, note: str) -> RuntimeResult:
    result = RuntimeResult(
        runtime="agent_zero",
        job_id=job_id,
        status="stub",
        output={"note": note},
        latency_ms=int((time.time() - t0) * 1000),
    )
    write_run_artifact(result)
    return result
