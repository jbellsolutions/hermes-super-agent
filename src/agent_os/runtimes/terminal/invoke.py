"""terminal runtime — plain shell scripts and cron-style jobs.

Picks up the shell command from one of (in order):
  job.metadata["shell_command"]    explicit, preferred
  job.metadata["script"]           alias
  job.prompt                       fallback — the prompt IS the command

Returns RuntimeResult with stdout/stderr/returncode bundled into .output.
Captures up to 64KB of each stream so a runaway log doesn't blow memory.

Safety:
- subprocess runs via /bin/sh -c so users can use pipes, redirects, &&.
  This is a `terminal` runtime; if you didn't want shell semantics you'd
  pick a different runtime.
- 5-minute default timeout. Override with metadata["timeout_seconds"].
- Working directory: metadata["cwd"] or current process cwd.
"""
from __future__ import annotations

import subprocess
import time
from typing import Any

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact

_DEFAULT_TIMEOUT_S = 300
_OUTPUT_CAP_BYTES = 64 * 1024


def invoke(job: Any) -> RuntimeResult:
    """Run job.metadata['shell_command'] (or .prompt) in /bin/sh."""
    t0 = time.time()
    job_id = new_job_id()

    metadata = _get_metadata(job)
    prompt = _get_attr(job, "prompt", "")
    cmd = (
        metadata.get("shell_command")
        or metadata.get("script")
        or prompt
        or ""
    ).strip()
    cwd = metadata.get("cwd") or None
    try:
        timeout_s = int(metadata.get("timeout_seconds", _DEFAULT_TIMEOUT_S))
    except (TypeError, ValueError):
        timeout_s = _DEFAULT_TIMEOUT_S

    if not cmd:
        result = RuntimeResult(
            runtime="terminal",
            job_id=job_id,
            status="error",
            error="no command supplied — set metadata['shell_command'] or use prompt as command",
            latency_ms=int((time.time() - t0) * 1000),
        )
        write_run_artifact(result)
        return result

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=cwd,
        )
        status = "completed" if proc.returncode == 0 else "error"
        output = {
            "stdout": _truncate(proc.stdout),
            "stderr": _truncate(proc.stderr),
            "returncode": proc.returncode,
            "command": cmd,
        }
        # Surface stdout at the top-level too so callers that just want
        # "the output" don't have to dig into a nested dict.
        flat_output = proc.stdout.strip()
        error = proc.stderr.strip() if proc.returncode != 0 else None
        result = RuntimeResult(
            runtime="terminal",
            job_id=job_id,
            status=status,
            output=flat_output if flat_output else output,
            error=error,
            latency_ms=int((time.time() - t0) * 1000),
        )
    except subprocess.TimeoutExpired:
        result = RuntimeResult(
            runtime="terminal",
            job_id=job_id,
            status="error",
            error=f"timeout after {timeout_s}s: {cmd}",
            latency_ms=int((time.time() - t0) * 1000),
        )
    except Exception as exc:
        result = RuntimeResult(
            runtime="terminal",
            job_id=job_id,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
            latency_ms=int((time.time() - t0) * 1000),
        )

    try:
        write_run_artifact(result)
    except Exception:
        # Artifact writing is best-effort — never let a vault permission
        # issue eat the actual run result.
        pass
    return result


def _get_metadata(job: Any) -> dict:
    """Tolerate Job dataclass, dict, or anything with .metadata."""
    if isinstance(job, dict):
        return job.get("metadata", {}) or {}
    meta = getattr(job, "metadata", None)
    return meta if isinstance(meta, dict) else {}


def _get_attr(job: Any, name: str, default: str = "") -> str:
    if isinstance(job, dict):
        return job.get(name, default) or default
    return getattr(job, name, default) or default


def _truncate(s: str) -> str:
    if not s:
        return ""
    encoded = s.encode("utf-8", errors="replace")
    if len(encoded) <= _OUTPUT_CAP_BYTES:
        return s
    return encoded[:_OUTPUT_CAP_BYTES].decode("utf-8", errors="replace") + "\n…[truncated]"
