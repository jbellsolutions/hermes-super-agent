"""VPS spawn runtime — thin adapter that delegates to orchestrator/spawner.py.

Invoked by dispatch() when job_router returns 'vps_spawn' (tags: spawn-superagent, vps-spawn).
All heavy lifting is in spawner.py which calls vps_provisioner + bootstrap.
"""
from __future__ import annotations

import logging
from typing import Any

from agent_os.orchestrator.adapters.job_router import Job

logger = logging.getLogger(__name__)


async def run(job: Job) -> dict[str, Any]:
    """Spawn a Tier 2 superagent VPS and bootstrap Hermes on it."""
    from agent_os.orchestrator.spawner import spawn
    return await spawn(job)
