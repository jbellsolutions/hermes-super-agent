"""Agent spawner — unified Tier 1 (Railway/Archon) and Tier 2 (VPS) spawning.

Tier 1: Specialist
  - Delegates to Archon (A2A endpoint) to generate AGENT.md + skill defs
  - Uses Railway API to deploy the generated spec as a new Railway service
  - Registers the new agent's A2A endpoint in vault/projects/registry.yaml
  - Subscribes to the new agent's NATS heartbeat

Tier 2: Superagent
  - Provisions a dedicated VPS (DigitalOcean or Hetzner)
  - Bootstraps Hermes + full Phase F orchestrator via SSH
  - Delegates sub-fleet creation back to the spawned superagent via A2A
  - Registers in registry.yaml and starts watching its aggregate NATS status

Usage:
    from agent_os.orchestrator.spawner import spawn
    result = await spawn(job)  # job.tags must include 'spawn-specialist' or 'spawn-superagent'
"""
from __future__ import annotations

import logging
import os
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import yaml

from agent_os.orchestrator.adapters.job_router import Job
from agent_os.bus.nats_publisher import publish_event

logger = logging.getLogger(__name__)

# Serialize all registry mutations within this process. Two simultaneous spawns
# (e.g., from Telegram + A2A POST) would otherwise read the same yaml, both
# append, and the second write would clobber the first.
_REGISTRY_LOCK = threading.Lock()

_ARCHON_URL = os.getenv("ARCHON_A2A_URL", "")
_RAILWAY_TOKEN = os.getenv("RAILWAY_API_TOKEN", "")
_RAILWAY_PROJECT_ID = os.getenv("RAILWAY_PROJECT_ID", "")
_REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "vault", "projects", "registry.yaml"
)


async def spawn(job: Job) -> dict[str, Any]:
    """Route to Tier 1 or Tier 2 spawning based on job tags."""
    tags = {t.lower() for t in job.tags}
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()

    publish_event("agents.admiral.task.started", {
        "task_id": task_id,
        "action": "spawn",
        "tags": list(tags),
    })

    if "spawn-superagent" in tags or "vps-spawn" in tags:
        result = await _spawn_tier2(job, task_id, t0)
    else:
        result = await _spawn_tier1(job, task_id, t0)

    event = "agents.admiral.task.completed" if result["status"] == "completed" \
        else "agents.admiral.task.failed"
    publish_event(event, {"task_id": task_id, "elapsed_seconds": result["elapsed_seconds"]})

    return result


# ---------------------------------------------------------------------------
# Tier 1: Specialist via Archon + Railway
# ---------------------------------------------------------------------------

async def _spawn_tier1(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """Generate a specialist spec via Archon and deploy it to Railway."""
    if not _ARCHON_URL:
        logger.warning("ARCHON_A2A_URL not set — returning dev stub for Tier 1 spawn")
        return _stub_result(task_id, "tier1-specialist", t0, note="ARCHON_A2A_URL not set")

    # Step 1: delegate spec generation to Archon via A2A
    archon_task_id = str(uuid.uuid4())
    spec = await _archon_generate(job, archon_task_id)
    if "error" in spec:
        return _error_result(task_id, f"Archon generation failed: {spec['error']}", t0)

    agent_id = spec.get("agent_id") or _slugify(job.prompt[:40])
    agent_md = spec.get("agent_md", "")
    tags = spec.get("tags", list(job.tags))

    # Step 2: deploy to Railway (if token is set)
    railway_service = ""
    if _RAILWAY_TOKEN and _RAILWAY_PROJECT_ID:
        railway_service = await _railway_deploy(agent_id, agent_md)

    # Step 3: register in registry.yaml
    a2a_endpoint = spec.get("a2a_endpoint", "")
    _register_agent(
        agent_id=agent_id,
        tier=1,
        runtime="hermes_self",
        tags=tags,
        a2a_endpoint=a2a_endpoint,
        railway_service=railway_service,
        model=spec.get("model", "claude-sonnet-4.7"),
        notes=f"Spawned by Admiral from prompt: {job.prompt[:100]}",
    )

    logger.info("Tier 1 specialist spawned: id=%s railway=%s", agent_id, railway_service)

    return {
        "status": "completed",
        "spawn_tier": 1,
        "agent_id": agent_id,
        "task_id": task_id,
        "railway_service": railway_service,
        "a2a_endpoint": a2a_endpoint,
        "elapsed_seconds": time.monotonic() - t0,
        "spec": spec,
    }


async def _archon_generate(job: Job, archon_task_id: str) -> dict[str, Any]:
    """POST to Archon A2A /messages and poll /tasks/{id} for the generated spec."""
    payload = {
        "parts": [{"kind": "text", "text": job.prompt}],
        "taskId": archon_task_id,
        "metadata": {"runtime": "archon_builder", "tags": ",".join(job.tags)},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(f"{_ARCHON_URL}/messages", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            return {"error": str(exc)}

        remote_id = resp.json().get("taskId", archon_task_id)

        # Poll up to 10 minutes
        for _ in range(120):
            import asyncio
            await asyncio.sleep(5)
            try:
                status_resp = await client.get(f"{_ARCHON_URL}/tasks/{remote_id}")
                status_resp.raise_for_status()
            except httpx.HTTPError:
                continue

            data = status_resp.json()
            state = data.get("status", {}).get("state", "unknown")
            if state == "completed":
                return data.get("result", {})
            if state in ("failed", "cancelled"):
                return {"error": data.get("result", {}).get("error", "archon failed")}

    return {"error": "archon timeout after 600s"}


async def _railway_deploy(agent_id: str, agent_md: str) -> str:
    """Create a Railway service for the new specialist. Returns service name."""
    if not _RAILWAY_TOKEN:
        return ""

    mutation = """
    mutation CreateService($projectId: String!, $name: String!) {
        serviceCreate(input: { projectId: $projectId, name: $name }) {
            id
            name
        }
    }
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://backboard.railway.app/graphql/v2",
                json={
                    "query": mutation,
                    "variables": {
                        "projectId": _RAILWAY_PROJECT_ID,
                        "name": agent_id,
                    },
                },
                headers={"Authorization": f"Bearer {_RAILWAY_TOKEN}"},
            )
            resp.raise_for_status()
            data = resp.json()
            service = data.get("data", {}).get("serviceCreate", {})
            return service.get("name", agent_id)
        except httpx.HTTPError as exc:
            logger.error("Railway deploy failed for %s: %s", agent_id, exc)
            return ""


# ---------------------------------------------------------------------------
# Tier 2: Superagent via VPS provisioner + SSH bootstrap
# ---------------------------------------------------------------------------

async def _spawn_tier2(job: Job, task_id: str, t0: float) -> dict[str, Any]:
    """Provision a VPS and bootstrap a full Hermes orchestrator on it."""
    from agent_os.orchestrator.vps_provisioner import provision
    from agent_os.orchestrator.bootstrap import bootstrap

    agent_id = job.metadata.get("agent_id") or _slugify(job.prompt[:40]) + "-superagent"

    # Step 1: provision VPS
    publish_event("agents.admiral.task.progress", {
        "task_id": task_id,
        "step": "vps_provision",
        "agent_id": agent_id,
    })
    vps = await provision(agent_id=agent_id, metadata=job.metadata)
    if vps.get("status") == "error":
        return _error_result(task_id, f"VPS provision failed: {vps['error']}", t0)

    vps_ip = vps["ip"]
    logger.info("VPS provisioned for %s: ip=%s", agent_id, vps_ip)

    # Step 2: SSH bootstrap
    publish_event("agents.admiral.task.progress", {
        "task_id": task_id,
        "step": "bootstrap",
        "agent_id": agent_id,
        "vps_ip": vps_ip,
    })
    boot = await bootstrap(
        agent_id=agent_id,
        vps_ip=vps_ip,
        mission=job.prompt,
        metadata=job.metadata,
    )
    if boot.get("status") == "error":
        # Bootstrap failed but the VPS is alive — we'd otherwise leak a paid
        # droplet. Record it in the registry as "bootstrap_failed" with the IP
        # and provider so the user can find and delete it. Don't auto-delete:
        # the user might want to SSH in to debug.
        provider = vps.get("provider", "unknown")
        server_id = vps.get("server_id", "unknown")
        cleanup_hint = _cleanup_hint(provider, server_id, vps_ip)
        try:
            _register_agent(
                agent_id=agent_id,
                tier=2,
                runtime="vps_spawn",
                tags=list(job.tags),
                a2a_endpoint="",
                vps_ip=vps_ip,
                model=job.metadata.get("model", ""),
                notes=f"BOOTSTRAP FAILED. {boot.get('error', '')}\n{cleanup_hint}",
            )
            # Patch the entry's status (registry sets 'active' by default)
            _patch_agent_status(agent_id, "bootstrap_failed")
        except Exception:
            logger.exception("Failed to record orphan VPS in registry")
        publish_event("agents.admiral.alert", {
            "task_id": task_id,
            "agent_id": agent_id,
            "needs_human": True,
            "error": f"Bootstrap failed; orphan VPS at {vps_ip} ({provider}:{server_id})",
        })
        return _error_result(
            task_id,
            f"Bootstrap failed: {boot['error']}. Orphan VPS at {vps_ip}. {cleanup_hint}",
            t0,
        )

    a2a_endpoint = f"http://{vps_ip}:{boot.get('a2a_port', 8080)}"

    # Step 3: register in registry.yaml
    _register_agent(
        agent_id=agent_id,
        tier=2,
        runtime="vps_spawn",
        tags=list(job.tags),
        a2a_endpoint=a2a_endpoint,
        vps_ip=vps_ip,
        model=job.metadata.get("model", "deepseek-v4-pro"),
        notes=f"Superagent spawned by Admiral. Mission: {job.prompt[:100]}",
    )

    # Step 4: delegate sub-fleet creation back to the superagent via A2A
    sub_fleet_prompt = job.metadata.get("sub_fleet_prompt", "")
    if sub_fleet_prompt:
        publish_event("agents.admiral.task.progress", {
            "task_id": task_id,
            "step": "sub_fleet_delegation",
            "agent_id": agent_id,
        })
        await _delegate_sub_fleet(a2a_endpoint, sub_fleet_prompt)

    logger.info("Tier 2 superagent spawned: id=%s vps=%s a2a=%s", agent_id, vps_ip, a2a_endpoint)

    return {
        "status": "completed",
        "spawn_tier": 2,
        "agent_id": agent_id,
        "task_id": task_id,
        "vps_ip": vps_ip,
        "a2a_endpoint": a2a_endpoint,
        "elapsed_seconds": time.monotonic() - t0,
    }


async def _delegate_sub_fleet(a2a_endpoint: str, sub_fleet_prompt: str) -> None:
    """Ask the newly spawned superagent to create its own sub-fleet via A2A."""
    payload = {
        "parts": [{"kind": "text", "text": sub_fleet_prompt}],
        "taskId": str(uuid.uuid4()),
        "metadata": {"tags": "build-specialist,spawn-specialist"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            await client.post(f"{a2a_endpoint}/messages", json=payload)
        except httpx.HTTPError as exc:
            logger.warning("Sub-fleet delegation failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------

def _register_agent(
    *,
    agent_id: str,
    tier: int,
    runtime: str,
    tags: list[str],
    a2a_endpoint: str = "",
    vps_ip: str = "",
    railway_service: str = "",
    model: str = "claude-sonnet-4.7",
    notes: str = "",
) -> None:
    """Append or update an agent entry in vault/projects/registry.yaml.

    Concurrency: serialized via _REGISTRY_LOCK so two parallel spawns can't
    interleave their read-modify-write cycles. Atomic rename guarantees a
    reader (or a crashed writer) never sees a half-written file.
    """
    registry_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "vault", "projects", "registry.yaml")
    )

    with _REGISTRY_LOCK:
        try:
            with open(registry_path) as f:
                registry = yaml.safe_load(f) or {}
        except FileNotFoundError:
            registry = {}

        agents: list[dict] = registry.get("agents", [])

        # Remove stale entry if it exists
        agents = [a for a in agents if a.get("id") != agent_id]

        agents.append({
            "id": agent_id,
            "tier": tier,
            "runtime": runtime,
            "status": "active",
            "a2a_endpoint": a2a_endpoint,
            "nats_subject": f"agents.{agent_id}.*",
            "vps_ip": vps_ip,
            "railway_service": railway_service,
            "model": model,
            "tags": tags,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "admiral",
            "notes": notes,
        })

        registry["agents"] = agents

        # Atomic write: tmp file in same dir → rename. POSIX rename is atomic.
        registry_dir = os.path.dirname(registry_path)
        os.makedirs(registry_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=registry_dir)
        try:
            with os.fdopen(fd, "w") as f:
                yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            os.replace(tmp_path, registry_path)
        except Exception:
            # Clean up tmp on failure so we don't accumulate orphans
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    logger.info("Registry updated: agent_id=%s tier=%s", agent_id, tier)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _stub_result(task_id: str, spawn_type: str, t0: float, note: str = "") -> dict[str, Any]:
    return {
        "status": "completed",
        "spawn_tier": spawn_type,
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "note": f"dev stub — {note}",
    }


def _error_result(task_id: str, error: str, t0: float) -> dict[str, Any]:
    return {
        "status": "error",
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "error": error,
    }


def _cleanup_hint(provider: str, server_id: str, vps_ip: str) -> str:
    """Print the exact command to delete an orphan VPS for the given provider."""
    if provider == "digitalocean":
        return f"To delete: doctl compute droplet delete {server_id}"
    if provider == "hetzner":
        return f"To delete: hcloud server delete {server_id}"
    return f"Manually delete the {provider} VPS at {vps_ip}"


def _patch_agent_status(agent_id: str, new_status: str) -> None:
    """Update the status field of an existing registry entry. Best-effort."""
    registry_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "vault", "projects", "registry.yaml")
    )
    try:
        with _REGISTRY_LOCK:
            with open(registry_path) as f:
                registry = yaml.safe_load(f) or {}
            for a in registry.get("agents", []):
                if a.get("id") == agent_id:
                    a["status"] = new_status
                    break
            with open(registry_path, "w") as f:
                yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except Exception as exc:
        logger.warning("Could not patch agent status for %s: %s", agent_id, exc)
