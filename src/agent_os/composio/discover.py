"""Discover Composio tools matching a natural-language query.

Hermes calls this when it thinks "I need a tool for X." Returns a ranked list
of tool slugs + schemas that match. Hermes picks one and calls composio.call().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from agent_os.composio.client import _base, _headers, _timeout, is_configured


@dataclass
class ToolMatch:
    slug: str
    name: str
    app: str
    description: str
    schema: dict[str, Any]


def discover(query: str, limit: int = 10) -> list[ToolMatch]:
    """Search the Composio catalog. Returns tools matching the query.

    Catalog is queried live — no nightly cache. Composio adds connectors
    frequently and we want them immediately discoverable.
    """
    if not is_configured():
        return []

    with httpx.Client(timeout=_timeout()) as c:
        r = c.get(
            f"{_base()}/api/v3/tools",
            headers=_headers(),
            params={"search": query, "limit": str(limit)},
        )
    if r.is_error:
        return []

    items = r.json().get("items") or r.json().get("data") or []
    out: list[ToolMatch] = []
    for it in items[:limit]:
        out.append(
            ToolMatch(
                slug=it.get("slug") or it.get("name", ""),
                name=it.get("displayName") or it.get("name", ""),
                app=it.get("appName") or it.get("app", ""),
                description=it.get("description", ""),
                schema=it.get("parameters") or it.get("input_parameters") or {},
            )
        )
    return out


def list_apps(query: str | None = None) -> list[dict[str, Any]]:
    """List Composio apps (Slack, Linear, Gmail, etc.). Optional query filter."""
    if not is_configured():
        return []
    params = {"search": query} if query else {}
    with httpx.Client(timeout=_timeout()) as c:
        r = c.get(f"{_base()}/api/v3/apps", headers=_headers(), params=params)
    if r.is_error:
        return []
    return r.json().get("items") or r.json().get("data") or []
