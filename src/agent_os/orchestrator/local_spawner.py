"""Local Docker spawner — Kaioken's counterpart to spawner._spawn_tier2.

Spawns a `hermes-superagent-<id>` container from the same root Dockerfile
the Admiral uses. The container joins the `hermes-fabric` Docker network
so Admiral can reach it by name, registers in vault/projects/registry.yaml,
and starts its A2A server on its own port inside the network.

Contract is identical to vps_spawn so the planner / Admiral can't tell
the difference: returns
    {
        "status": "completed",
        "spawn_tier": 2,
        "agent_id": str,
        "task_id": str,
        "a2a_endpoint": "http://<container_name>:8080",
        "elapsed_seconds": float,
        "container_id": str,         # local-spawn extra
        "container_name": str,       # local-spawn extra
    }

Failure modes:
- Docker daemon not running          → status=error, error="docker daemon unreachable"
- Image hermes-superagent not built  → tries `docker build` from repo root,
                                       errors out cleanly if that fails too
- Container health-check timeout     → tears the container down, returns error

This module imports `docker` lazily so saiyan-mode installs (which never
call into this file) don't need the `docker` Python package on disk.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from agent_os.orchestrator.adapters.job_router import Job

logger = logging.getLogger(__name__)

# Docker network created by docker-compose.kaioken.yml. All Hermes
# containers (admiral, coordinator, nats, temporal, spawned superagents)
# share it so they can reach each other by service name.
_NETWORK = os.getenv("HERMES_DOCKER_NETWORK", "hermes-fabric")

# Image tag the Kaioken installer builds during `kaioken-up.sh`. Same
# Dockerfile as the Admiral — superagents differ only in the env they're
# launched with (HERMES_ROLE=worker, identity, parent A2A URL).
_IMAGE = os.getenv("HERMES_SUPERAGENT_IMAGE", "hermes-superagent:latest")

# Max seconds to wait for the spawned container's /agentCard to respond 200.
_HEALTH_TIMEOUT = int(os.getenv("HERMES_LOCAL_SPAWN_HEALTH_TIMEOUT", "60"))


async def spawn_local(job: Job) -> dict[str, Any]:
    """Spawn a Tier 2 superagent as a local container. See module docstring."""
    task_id = str(uuid.uuid4())
    t0 = time.monotonic()

    try:
        import docker  # type: ignore[import-untyped]
    except ImportError:
        return _err(task_id, t0, "docker SDK not installed — `pip install docker`")

    try:
        client = docker.from_env()
        client.ping()
    except Exception as exc:  # docker.errors.DockerException + friends
        return _err(task_id, t0, f"docker daemon unreachable: {exc}")

    agent_id = (
        job.metadata.get("agent_id")
        or _slugify(job.prompt[:40]) + "-superagent"
    )
    container_name = f"hermes-superagent-{agent_id[:40]}-{task_id[:8]}"
    identity = job.metadata.get("identity", "primary_hermes")
    parent_a2a = job.metadata.get("parent_a2a", "http://hermes-admiral:8080")

    # Build the image if it's missing. First Kaioken spawn pays this cost
    # (~30s); subsequent spawns are instant.
    if not _image_exists(client, _IMAGE):
        logger.info("Image %s not found — building from repo root", _IMAGE)
        try:
            await asyncio.to_thread(_build_image, client, _IMAGE)
        except Exception as exc:
            return _err(task_id, t0, f"docker build failed: {exc}")

    # Ensure the network exists. docker-compose.kaioken.yml creates it,
    # but if the user is spawning before bringing the compose stack up
    # we create it on demand so the spawn doesn't 500.
    try:
        await asyncio.to_thread(_ensure_network, client, _NETWORK)
    except Exception as exc:
        return _err(task_id, t0, f"could not ensure network {_NETWORK}: {exc}")

    # Spawn. Pass enough env that the container can boot a worker Hermes
    # and register back with the parent Admiral via A2A.
    spawn_env = {
        "HERMES_ROLE": "worker",
        "HERMES_AGENT_ID": agent_id,
        "HERMES_IDENTITY": identity,
        "HERMES_PARENT_A2A": parent_a2a,
        "HERMES_MODE": "kaioken",
        # Forward LLM keys if set on the host; the spawned worker needs them.
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
        "MOONSHOT_API_KEY": os.getenv("MOONSHOT_API_KEY", ""),
        "NATS_URL": os.getenv("NATS_URL", "nats://hermes-nats:4222"),
        "TEMPORAL_HOST": os.getenv("TEMPORAL_HOST", "hermes-temporal:7233"),
        "COORDINATOR_URL": os.getenv("COORDINATOR_URL", "http://hermes-coordinator:8000"),
    }

    # Publish the container's :8080 to a random host port so the demo (which
    # runs OUTSIDE the docker network from the user's laptop) can probe the
    # spawned worker. From inside the network (Admiral container reaching its
    # children), service-name resolution still works via the bridge net.
    try:
        container = await asyncio.to_thread(
            client.containers.run,
            _IMAGE,
            detach=True,
            name=container_name,
            network=_NETWORK,
            environment=spawn_env,
            ports={"8080/tcp": None},   # None = bind to random free host port
            labels={
                "hermes.role": "superagent",
                "hermes.agent_id": agent_id,
                "hermes.spawn_task_id": task_id,
                "hermes.identity": identity,
            },
            restart_policy={"Name": "unless-stopped"},
        )
    except Exception as exc:
        return _err(task_id, t0, f"docker run failed: {exc}")

    # In-network endpoint (Admiral → child via service name on the bridge).
    a2a_endpoint = f"http://{container_name}:8080"
    # Host-visible endpoint (for the spawn demo running on the user's laptop).
    host_endpoint = await _resolve_host_endpoint(container)
    logger.info("Spawned %s (id=%s) on net=%s host=%s",
                container_name, container.id[:12], _NETWORK, host_endpoint)

    # Probe health using whichever endpoint we can actually reach. From inside
    # the Admiral container, _NETWORK resolution works → use a2a_endpoint.
    # From the host (the demo case), service names don't resolve → use the
    # host_endpoint we just published.
    probe_target = a2a_endpoint if _running_inside_fabric() else (host_endpoint or a2a_endpoint)
    healthy = await _wait_for_healthy(probe_target, _HEALTH_TIMEOUT)
    if not healthy:
        logger.warning("Container %s did not become healthy in %ss — tearing down",
                       container_name, _HEALTH_TIMEOUT)
        try:
            await asyncio.to_thread(container.stop, timeout=5)
            await asyncio.to_thread(container.remove)
        except Exception:
            logger.exception("Cleanup failed for %s", container_name)
        return _err(task_id, t0,
                    f"container {container_name} did not respond on /agentCard "
                    f"within {_HEALTH_TIMEOUT}s")

    # Best-effort registry update. We import lazily because the registry
    # helpers live in spawner.py, which depends on the bus module — fine
    # in Kaioken (bus is up), missing in Saiyan (saiyan doesn't ship bus,
    # but saiyan_overrides blocks this codepath anyway).
    try:
        from agent_os.orchestrator.spawner import _register_agent  # type: ignore
        _register_agent(
            agent_id=agent_id,
            tier=2,
            runtime="local_spawn",
            tags=list(job.tags),
            a2a_endpoint=a2a_endpoint,
            model=job.metadata.get("model", "deepseek-v4-pro"),
            notes=(
                f"Kaioken local-spawn. Container: {container_name}. "
                f"Mission: {job.prompt[:100]}"
            ),
        )
    except Exception:
        logger.exception("Registry update failed (non-fatal)")

    return {
        "status": "completed",
        "spawn_tier": 2,
        "agent_id": agent_id,
        "task_id": task_id,
        "a2a_endpoint": a2a_endpoint,         # in-network (Admiral → child)
        "host_endpoint": host_endpoint,       # host-side (laptop → child)
        "elapsed_seconds": time.monotonic() - t0,
        "container_id": container.id,
        "container_name": container_name,
        "spawned_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _image_exists(client, tag: str) -> bool:
    try:
        client.images.get(tag)
        return True
    except Exception:
        return False


def _build_image(client, tag: str) -> None:
    """Build the Hermes image from the repo root Dockerfile."""
    # Repo root = three levels up from this file (src/agent_os/orchestrator).
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    client.images.build(path=repo_root, tag=tag, rm=True, pull=False)


def _ensure_network(client, name: str) -> None:
    existing = client.networks.list(names=[name])
    if existing:
        return
    client.networks.create(name, driver="bridge")


def _running_inside_fabric() -> bool:
    """Heuristic: are we executing inside a container on the docker network?

    True when HERMES_ROLE is set (Admiral / worker containers always set it),
    False when running from the host (the demo). We use the env signal rather
    than `/proc/1/cgroup` parsing because the env is the explicit contract —
    docker-compose.kaioken.yml sets HERMES_ROLE=admiral on the admiral service.
    """
    return bool(os.getenv("HERMES_ROLE"))


async def _resolve_host_endpoint(container) -> str | None:
    """After docker.run with ports={'8080/tcp': None}, look up the random host
    port the daemon assigned and return http://127.0.0.1:<port>. Returns None
    if the port mapping isn't ready yet (rare; container.reload retries)."""
    try:
        await asyncio.to_thread(container.reload)
        port_map = (container.attrs.get("NetworkSettings") or {}).get("Ports") or {}
        bindings = port_map.get("8080/tcp") or []
        if not bindings:
            return None
        host_port = bindings[0].get("HostPort")
        return f"http://127.0.0.1:{host_port}" if host_port else None
    except Exception:
        return None


async def _wait_for_healthy(a2a_endpoint: str, timeout_s: int) -> bool:
    """Poll /agentCard until 200 or timeout. Soft on connection errors —
    the container needs a few seconds to boot uvicorn before the port is open.
    """
    try:
        import httpx
    except ImportError:
        # If httpx isn't installed we can't probe; assume healthy after a
        # short grace period. Better to over-trust here than block install.
        await asyncio.sleep(min(timeout_s, 5))
        return True

    deadline = time.monotonic() + timeout_s
    async with httpx.AsyncClient(timeout=2) as client:
        while time.monotonic() < deadline:
            try:
                r = await client.get(f"{a2a_endpoint}/agentCard")
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
    return False


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "agent"


def _err(task_id: str, t0: float, error: str) -> dict[str, Any]:
    return {
        "status": "error",
        "task_id": task_id,
        "elapsed_seconds": time.monotonic() - t0,
        "error": error,
    }
