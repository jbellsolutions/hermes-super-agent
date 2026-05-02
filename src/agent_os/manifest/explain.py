"""Backend for the /explain Claude Code skill. Walks the graph in plain language."""
from __future__ import annotations

from agent_os.manifest.aggregator import build_graph


def whats_running() -> str:
    """TODO(stage-6): summarize Hermes heartbeat + active runtimes + current jobs."""
    return "Stage 6 not yet implemented — read vault/heartbeats/ directly."


def who_wrote(output_path: str) -> str:
    """TODO(stage-6): walk back from a vault output to the agent + prompt + run id."""
    return f"Stage 6 not yet implemented — output={output_path}"


def what_depends_on(component: str) -> list[str]:
    g = build_graph()
    return [e["from"] for e in g["edges"] if e["to"] == component and e["rel"] == "depends_on"]


def changed_in_last_24h() -> str:
    """TODO(stage-6): diff manifest snapshots day-over-day."""
    return "Stage 6 not yet implemented — check git log on packages/."
