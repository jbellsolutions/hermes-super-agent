"""VPS provisioner — DigitalOcean (primary) with Hetzner fallback.

Creates a Tier 2 superagent VPS:
  1. Pick provider (DO preferred, Hetzner if DO_API_TOKEN unset)
  2. Create droplet/server (Ubuntu 24.04, 2GB RAM minimum)
  3. Inject SSH public key at creation time
  4. Wait for the server to become reachable over SSH (~45 seconds typical)
  5. Return {ip, provider, server_id, status}

Callers (spawner.py) then hand the IP to bootstrap.py for the actual
Hermes install.

Usage:
    from agent_os.orchestrator.vps_provisioner import provision
    vps = await provision(agent_id="cold-email-superagent", metadata={...})
"""
from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DO_API_TOKEN = os.getenv("DO_API_TOKEN", "")
_HETZNER_API_TOKEN = os.getenv("HETZNER_API_TOKEN", "")
_SSH_KEY_FINGERPRINT = os.getenv("DO_SSH_KEY_FINGERPRINT", "")  # DO fingerprint
_HETZNER_SSH_KEY_ID = os.getenv("HETZNER_SSH_KEY_ID", "")       # Hetzner numeric ID

_DO_BASE = "https://api.digitalocean.com/v2"
_HETZNER_BASE = "https://api.hetzner.cloud/v1"

_SSH_TIMEOUT = 120  # seconds to wait for SSH reachability


async def provision(agent_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Provision a VPS for a Tier 2 superagent.

    Returns:
        {status: "completed"|"error", ip, provider, server_id, elapsed_seconds}
    """
    metadata = metadata or {}
    t0 = time.monotonic()

    size = metadata.get("vps_size", "")
    region = metadata.get("vps_region", "")

    if _DO_API_TOKEN:
        return await _provision_do(agent_id, size, region, t0)
    elif _HETZNER_API_TOKEN:
        return await _provision_hetzner(agent_id, size, region, t0)
    else:
        logger.warning("No VPS API token set (DO_API_TOKEN, HETZNER_API_TOKEN) — returning stub")
        return _stub_result(agent_id, t0)


# ---------------------------------------------------------------------------
# DigitalOcean
# ---------------------------------------------------------------------------

async def _provision_do(agent_id: str, size: str, region: str, t0: float) -> dict[str, Any]:
    size = size or "s-1vcpu-2gb"    # $12/mo, 2GB RAM, 1 vCPU
    region = region or "nyc3"

    payload: dict[str, Any] = {
        "name": agent_id,
        "region": region,
        "size": size,
        "image": "ubuntu-24-04-x64",
        "backups": False,
        "ipv6": False,
        "monitoring": True,
        "tags": ["hermes-fleet", agent_id],
    }
    if _SSH_KEY_FINGERPRINT:
        payload["ssh_keys"] = [_SSH_KEY_FINGERPRINT]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{_DO_BASE}/droplets",
                json=payload,
                headers={
                    "Authorization": f"Bearer {_DO_API_TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("DigitalOcean droplet creation failed: %s", exc)
            return {"status": "error", "error": str(exc), "elapsed_seconds": time.monotonic() - t0}

        droplet = resp.json().get("droplet", {})
        droplet_id = droplet.get("id")
        logger.info("DO droplet created: id=%s name=%s", droplet_id, agent_id)

        # Poll for active status + public IP
        ip = await _wait_for_do_ip(client, droplet_id)
        if not ip:
            return {
                "status": "error",
                "error": f"Droplet {droplet_id} did not get IP within 120s",
                "elapsed_seconds": time.monotonic() - t0,
            }

    # Wait for SSH port to open
    await _wait_for_ssh(ip)

    return {
        "status": "completed",
        "provider": "digitalocean",
        "server_id": str(droplet_id),
        "ip": ip,
        "size": size,
        "region": region,
        "elapsed_seconds": time.monotonic() - t0,
    }


async def _wait_for_do_ip(client: httpx.AsyncClient, droplet_id: int) -> str:
    """Poll DigitalOcean until the droplet has a public IPv4 address."""
    for _ in range(24):  # up to 2 minutes
        await asyncio.sleep(5)
        try:
            resp = await client.get(
                f"{_DO_BASE}/droplets/{droplet_id}",
                headers={"Authorization": f"Bearer {_DO_API_TOKEN}"},
            )
            resp.raise_for_status()
            droplet = resp.json().get("droplet", {})
            networks = droplet.get("networks", {}).get("v4", [])
            for net in networks:
                if net.get("type") == "public":
                    return net.get("ip_address", "")
        except httpx.HTTPError:
            continue
    return ""


# ---------------------------------------------------------------------------
# Hetzner
# ---------------------------------------------------------------------------

async def _provision_hetzner(agent_id: str, size: str, region: str, t0: float) -> dict[str, Any]:
    size = size or "cx22"   # €4.35/mo, 2GB RAM, 2 vCPU
    region = region or "nbg1"

    payload: dict[str, Any] = {
        "name": agent_id,
        "server_type": size,
        "location": region,
        "image": "ubuntu-24.04",
        "labels": {"fleet": "hermes", "agent": agent_id},
    }
    if _HETZNER_SSH_KEY_ID:
        payload["ssh_keys"] = [int(_HETZNER_SSH_KEY_ID)]

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{_HETZNER_BASE}/servers",
                json=payload,
                headers={
                    "Authorization": f"Bearer {_HETZNER_API_TOKEN}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Hetzner server creation failed: %s", exc)
            return {"status": "error", "error": str(exc), "elapsed_seconds": time.monotonic() - t0}

        data = resp.json()
        server = data.get("server", {})
        server_id = server.get("id")
        ip = server.get("public_net", {}).get("ipv4", {}).get("ip", "")
        logger.info("Hetzner server created: id=%s ip=%s", server_id, ip)

    if ip:
        await _wait_for_ssh(ip)
    else:
        return {
            "status": "error",
            "error": "Hetzner server has no public IP",
            "elapsed_seconds": time.monotonic() - t0,
        }

    return {
        "status": "completed",
        "provider": "hetzner",
        "server_id": str(server_id),
        "ip": ip,
        "size": size,
        "region": region,
        "elapsed_seconds": time.monotonic() - t0,
    }


# ---------------------------------------------------------------------------
# SSH reachability check
# ---------------------------------------------------------------------------

async def _wait_for_ssh(ip: str, port: int = 22, timeout: int = _SSH_TIMEOUT) -> None:
    """Block until port 22 is accepting connections on the given IP."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            sock = socket.create_connection((ip, port), timeout=3)
            sock.close()
            logger.info("SSH reachable at %s:%s", ip, port)
            return
        except (socket.timeout, ConnectionRefusedError, OSError):
            await asyncio.sleep(3)
    logger.warning("SSH not reachable at %s:%s after %ss — proceeding anyway", ip, port, timeout)


# ---------------------------------------------------------------------------
# Dev stub
# ---------------------------------------------------------------------------

def _stub_result(agent_id: str, t0: float) -> dict[str, Any]:
    return {
        "status": "completed",
        "provider": "stub",
        "server_id": "stub-0",
        "ip": "127.0.0.1",
        "elapsed_seconds": time.monotonic() - t0,
        "note": f"dev stub for {agent_id} — set DO_API_TOKEN or HETZNER_API_TOKEN",
    }
