"""Composio REST client — auth + tool invocation.

Uses httpx directly against Composio's v3 API. No vendor SDK dependency.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact


def _base() -> str:
    return os.environ.get("COMPOSIO_BASE_URL", "https://backend.composio.dev")


def _key() -> str:
    return os.environ.get("COMPOSIO_API_KEY", "")


def _timeout() -> float:
    return float(os.environ.get("COMPOSIO_TIMEOUT", "60"))


# Backwards-compatible module-level constants (read once at import)
COMPOSIO_BASE = _base()
TIMEOUT = _timeout()


def is_configured() -> bool:
    return bool(_key())


def _headers() -> dict[str, str]:
    k = _key()
    if not k:
        raise RuntimeError(
            "COMPOSIO_API_KEY not set. Add it to .env or run scripts/launch.py."
        )
    return {"x-api-key": k, "content-type": "application/json"}


@dataclass
class CallResult:
    tool: str
    status: str  # "ok" | "error" | "not-connected" | "not-configured"
    output: Any = None
    error: str | None = None
    needs_connection_for: str | None = None  # app slug if status == "not-connected"


def call(tool: str, args: dict | None = None, connection_id: str | None = None) -> CallResult:
    """Invoke a Composio tool by slug. Logs the call to vault/runs/.

    If the tool's app has no connection yet, returns status='not-connected' and
    sets needs_connection_for so Hermes can offer to connect.connect(app) and retry.
    """
    if not is_configured():
        return CallResult(tool=tool, status="not-configured", error="COMPOSIO_API_KEY missing")

    payload: dict[str, Any] = {"arguments": args or {}}
    if connection_id:
        payload["connectedAccountId"] = connection_id

    job_id = new_job_id()
    try:
        with httpx.Client(timeout=_timeout()) as c:
            r = c.post(
                f"{_base()}/api/v3/tools/{tool}/execute",
                headers=_headers(),
                json=payload,
            )
        if r.status_code == 401:
            err = "auth failed — check COMPOSIO_API_KEY"
            result = CallResult(tool=tool, status="error", error=err)
        elif r.status_code in (404, 412) and "connect" in r.text.lower():
            app = tool.split("_", 1)[0] if "_" in tool else tool
            result = CallResult(tool=tool, status="not-connected", needs_connection_for=app)
        elif r.is_error:
            result = CallResult(tool=tool, status="error", error=r.text[:500])
        else:
            data = r.json()
            result = CallResult(tool=tool, status="ok", output=data)
    except httpx.RequestError as e:
        result = CallResult(tool=tool, status="error", error=f"network: {e}")

    write_run_artifact(
        RuntimeResult(
            runtime="composio",
            job_id=job_id,
            status=result.status,
            output={"tool": tool, "result": result.output},
            error=result.error,
        )
    )
    return result
