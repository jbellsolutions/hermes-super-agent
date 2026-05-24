"""Local-spawn runtime — thin adapter that delegates to orchestrator/local_spawner.py.

Mirrors vps_spawn/invoke.py exactly. Invoked by dispatch() when
job_router returns 'local_spawn' (Kaioken mode + tags: spawn-superagent
or vps-spawn). All heavy lifting is in local_spawner.py which talks to
the Docker SDK.
"""
from __future__ import annotations

import logging
from typing import Any

from agent_os.orchestrator.adapters.job_router import Job

logger = logging.getLogger(__name__)


async def run(job: Job) -> dict[str, Any]:
    """Spawn a Tier 2 superagent as a local Docker container."""
    from agent_os.orchestrator.local_spawner import spawn_local
    return await spawn_local(job)
