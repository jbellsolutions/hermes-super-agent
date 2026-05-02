"""Specialist runtimes Hermes routes to per job tags.

Each runtime is a thin adapter exposing `invoke(job) -> result`. The
job_router in agent_os.orchestrator.adapters.job_router decides which one
gets called.
"""

__version__ = "0.1.0"
