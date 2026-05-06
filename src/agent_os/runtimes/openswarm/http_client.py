"""Thin HTTP client for OpenSwarm's agency-swarm FastAPI server.

OpenSwarm's `server.py` exposes one agency (default name: `open-swarm`) via
`agency_swarm.integrations.fastapi.run_fastapi`. The standard endpoint is
`POST /<agency>/get_completion` taking `{message, attachments?, ...}` and
returning the agency's response. Streaming variant: `/get_completion_stream`.

If the upstream API surface changes, only this module needs edits; fleet.py
uses the functions exported here.
"""
from __future__ import annotations

from typing import Any

import httpx


class SwarmHTTPError(RuntimeError):
    pass


def _url(port: int, agency: str, suffix: str) -> str:
    return f"http://127.0.0.1:{port}/{agency}/{suffix}"


def health(port: int, *, timeout: float = 2.0) -> bool:
    """Best-effort liveness probe. Hits `/` — agency-swarm returns 404 there
    but a live server gets us a 4xx, while a dead one raises."""
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/", timeout=timeout)
    except httpx.HTTPError:
        return False
    return r.status_code < 500


def get_completion(
    port: int,
    *,
    agency: str = "open-swarm",
    message: str,
    attachments: list[str] | None = None,
    agent: str | None = None,
    timeout: float = 1800.0,
) -> dict[str, Any]:
    """POST a prompt to the agency. `agent` is optional; when omitted the
    agency's orchestrator picks the specialist."""
    payload: dict[str, Any] = {"message": message}
    if attachments:
        payload["attachments"] = attachments
    if agent and agent != "auto":
        payload["recipient_agent"] = agent
    try:
        r = httpx.post(_url(port, agency, "get_completion"), json=payload, timeout=timeout)
    except httpx.HTTPError as e:
        raise SwarmHTTPError(f"openswarm @{port} unreachable: {e}") from e
    if r.status_code >= 400:
        raise SwarmHTTPError(
            f"openswarm @{port} returned {r.status_code}: {r.text[:500]}"
        )
    try:
        return r.json()
    except ValueError:
        return {"raw": r.text}
