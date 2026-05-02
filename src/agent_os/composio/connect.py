"""Initiate and persist Composio app connections (OAuth flows).

When Hermes hits a 'not-connected' result from composio.call(), it calls
connect(app) which returns an OAuth URL. Hermes posts that URL to the user
in whichever channel they're on, then polls for completion. Once connected,
the connection ID is persisted to vault/composio/connections.yaml so future
calls skip the connection check.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml

from agent_os.composio.client import _base, _headers, _timeout, is_configured


def _connections_file() -> Path:
    root = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()
    return root / "composio" / "connections.yaml"


@dataclass
class ConnectionRequest:
    app: str
    status: str  # "pending" | "connected" | "error" | "not-configured"
    connection_id: str | None = None
    redirect_url: str | None = None
    error: str | None = None


def _load_connections() -> dict[str, str]:
    f = _connections_file()
    if not f.exists():
        return {}
    data = yaml.safe_load(f.read_text()) or {}
    return data if isinstance(data, dict) else {}


def _save_connections(connections: dict[str, str]) -> None:
    f = _connections_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(yaml.safe_dump(connections, sort_keys=True))


def list_connections() -> dict[str, str]:
    """Return {app: connection_id} from vault/composio/connections.yaml."""
    return _load_connections()


def connect(app: str, redirect_uri: str | None = None) -> ConnectionRequest:
    """Initiate an OAuth flow for `app` (e.g. 'slack', 'linear', 'gmail').

    Returns a ConnectionRequest with redirect_url. Hermes posts that URL to
    the user; after the user completes OAuth in their browser, call
    poll_connection(connection_id) until status='connected'.
    """
    if not is_configured():
        return ConnectionRequest(app=app, status="not-configured", error="COMPOSIO_API_KEY missing")

    payload: dict[str, str] = {"app": app}
    if redirect_uri:
        payload["redirectUri"] = redirect_uri

    try:
        with httpx.Client(timeout=_timeout()) as c:
            r = c.post(
                f"{_base()}/api/v3/connectedAccounts/initiate",
                headers=_headers(),
                json=payload,
            )
        if r.is_error:
            return ConnectionRequest(app=app, status="error", error=r.text[:500])
        data = r.json()
        return ConnectionRequest(
            app=app,
            status="pending",
            connection_id=data.get("id") or data.get("connectionId"),
            redirect_url=data.get("redirectUrl") or data.get("authorizeUrl"),
        )
    except httpx.RequestError as e:
        return ConnectionRequest(app=app, status="error", error=f"network: {e}")


def poll_connection(
    connection_id: str,
    timeout_seconds: int = 300,
    app: str | None = None,
) -> ConnectionRequest:
    """Poll until the OAuth flow completes (or timeout). Persists on success."""
    if not is_configured():
        return ConnectionRequest(app=app or "?", status="not-configured")

    deadline = time.time() + timeout_seconds
    last_status: str = "pending"
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=_timeout()) as c:
                r = c.get(
                    f"{_base()}/api/v3/connectedAccounts/{connection_id}",
                    headers=_headers(),
                )
            if r.is_error:
                return ConnectionRequest(
                    app=app or "?", status="error", connection_id=connection_id, error=r.text[:500]
                )
            data = r.json()
            status = (data.get("status") or "").lower()
            last_status = status
            resolved_app = data.get("appName") or data.get("app") or app or "?"
            if status in ("active", "connected"):
                conns = _load_connections()
                conns[resolved_app] = connection_id
                _save_connections(conns)
                return ConnectionRequest(
                    app=resolved_app, status="connected", connection_id=connection_id
                )
            if status in ("failed", "expired", "revoked"):
                return ConnectionRequest(
                    app=resolved_app,
                    status="error",
                    connection_id=connection_id,
                    error=f"oauth ended with status={status}",
                )
        except httpx.RequestError as e:
            return ConnectionRequest(
                app=app or "?", status="error", connection_id=connection_id, error=f"network: {e}"
            )
        time.sleep(2)
    return ConnectionRequest(
        app=app or "?",
        status="error",
        connection_id=connection_id,
        error=f"timeout after {timeout_seconds}s; last status={last_status}",
    )
