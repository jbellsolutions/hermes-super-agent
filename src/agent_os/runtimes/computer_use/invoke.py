"""computer_use runtime invoke entry point."""
from __future__ import annotations

import time

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact


def invoke(job: dict) -> RuntimeResult:
    """TODO: wire computer_use.

    Raw OS-level desktop + browser via Anthropic Computer Use SDK.
    """
    t0 = time.time()
    result = RuntimeResult(
        runtime="computer_use",
        job_id=new_job_id(),
        status="stub",
        output={"note": "stub — see ARCHITECTURE.md routing rules"},
        latency_ms=int((time.time() - t0) * 1000),
    )
    write_run_artifact(result)
    return result
