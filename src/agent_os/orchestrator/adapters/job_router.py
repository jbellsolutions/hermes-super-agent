"""Decide which runtime handles a given job, based on tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RuntimeName = Literal[
    "hermes_self",       # default — Hermes handles it itself with sub-agents
    "openclaw",          # autonomous-grind, shell, file-ops
    "openswarm",         # multi-agent deliverables (slides/decks/docs/charts) + builder
    "browser_use",       # structured browser
    "agent_zero",        # visual/autonomous browser UI + A0 host bridge
    "computer_use",      # raw desktop
    "claude_subagents",  # interactive coding
    "codex_cli",         # background coding
    "aider",             # git-aware incremental coding
    "claude_managed",    # long-running cloud
    "e2b",               # sandboxed code execution
    "exa",               # neural search
    "livekit",           # voice/realtime (channel-handled)
    "terminal",          # plain cron-style scripts
    # Fabric runtimes — external A2A endpoints and VPS provisioner
    "a2a_delegate",      # delegate entire job to an external A2A agent endpoint
    "vps_spawn",         # provision a new Tier 2 superagent on a dedicated VPS
    "kimi_coordinator",  # fan-out to Kimi K2.6 300-agent swarm via Moonshot API
    "retell_channel",    # outbound phone via Retell AI
]


@dataclass
class Job:
    prompt: str
    tags: set[str] = field(default_factory=set)
    estimated_minutes: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def route(job: Job) -> RuntimeName:
    """Map a Job's tags to the runtime that should handle it.

    Default-to-Hermes is intentional: most work shouldn't need a specialist.
    Tag rules below match ARCHITECTURE.md.
    """
    t = {tag.lower() for tag in job.tags}

    # Fabric runtimes — checked first; these handle cross-agent orchestration.
    # Kimi K2.6 Swarm Coordinator: 300-agent fan-out, Temporal-wrapped.
    if "fan-out" in t or "kimi" in t or "swarm-coordinator" in t:
        return "kimi_coordinator"
    # VPS superagent spawning — full Hermes + orchestrator on a dedicated droplet.
    if "spawn-superagent" in t or "vps-spawn" in t:
        return "vps_spawn"
    # Archon agent builder — delegates "create a specialist" to Archon A2A endpoint.
    if "build-specialist" in t or "archon" in t:
        return "a2a_delegate"
    # Retell AI phone channel.
    if "phone" in t or "retell" in t or "outbound-phone" in t:
        return "retell_channel"
    # Generic A2A delegation — when job explicitly targets a named external agent.
    if "a2a" in t or "delegate" in t:
        return "a2a_delegate"

    # OpenSwarm: multi-agent deliverable production (slides+research+docs+charts)
    # and the agent-builder ("build me a swarm for X"). Per-swarm semantic routing
    # is layered on top via vault/skills/active/<swarm>-swarm.md.
    if "build-swarm" in t or "new-swarm" in t:
        return "openswarm"
    if {"multi-deliverable", "slides+research+docs", "investor-pitch", "pitch-deck"} & t:
        return "openswarm"
    if "swarm" in t or "openswarm" in t:
        return "openswarm"

    if "coding" in t and "interactive" in t:
        return "claude_subagents"
    if "coding" in t and ("background" in t or "codex" in t):
        return "codex_cli"
    if "coding" in t and ("git-incremental" in t or "aider" in t):
        return "aider"
    if "agent-zero" in t or "agent_zero" in t or ({"visual", "autonomous-ui"} & t):
        return "agent_zero"
    if "browser" in t and ("structured" in t or "web-task" in t):
        return "browser_use"
    if {"autonomous-grind", "shell", "file-ops"} & t:
        return "openclaw"
    if "raw-desktop" in t or "native-app" in t:
        return "computer_use"
    if "long-running" in t or "cloud" in t or (
        job.estimated_minutes is not None and job.estimated_minutes > 60
    ):
        return "claude_managed"
    if "sandboxed-code" in t or "exec-untrusted" in t:
        return "e2b"
    if "search" in t and ("articles" in t or "quick-lookup" in t):
        return "exa"
    if "voice" in t or "realtime" in t:
        return "livekit"
    if "script" in t or "cron" in t:
        return "terminal"
    return "hermes_self"


def plan_for(job: Job, *, identity: str = "primary_hermes"):
    """Convenience: route() + tool_planner.plan() in one call.

    Returns a ToolPlan dataclass. Imported lazily so the router stays usable
    without the catalog (e.g. for the existing /route CLI which only needs
    the runtime name).
    """
    from agent_os.orchestrator.tool_planner import plan
    return plan(job, identity=identity)


async def dispatch(job: Job):
    """Route job → correct runtime module → call run(job).

    All fabric runtimes (kimi_coordinator, retell_channel, vps_spawn,
    a2a_delegate) expose `async def run(job)`. Legacy runtimes that only
    have a sync `invoke(job)` are wrapped with asyncio.to_thread.
    """
    import asyncio
    runtime = route(job)

    _ASYNC_RUNTIMES = {
        "kimi_coordinator": "agent_os.runtimes.kimi_coordinator.invoke",
        "retell_channel":   "agent_os.runtimes.retell_channel.invoke",
        "vps_spawn":        "agent_os.runtimes.vps_spawn.invoke",
        "a2a_delegate":     "agent_os.runtimes.a2a_delegate.invoke",
    }
    _SYNC_RUNTIMES = {
        "openclaw":        "agent_os.runtimes.openclaw.invoke",
        "openswarm":       "agent_os.runtimes.openswarm.invoke",
        "browser_use":     "agent_os.runtimes.browser_use.invoke",
        "agent_zero":      "agent_os.runtimes.agent_zero.invoke",
        "computer_use":    "agent_os.runtimes.computer_use.invoke",
        "claude_subagents":"agent_os.runtimes.claude_subagents.invoke",
        "codex_cli":       "agent_os.runtimes.codex_cli.invoke",
        "aider":           "agent_os.runtimes.aider.invoke",
        "claude_managed":  "agent_os.runtimes.claude_managed.invoke",
        "e2b":             "agent_os.runtimes.e2b.invoke",
        "exa":             "agent_os.runtimes.exa.invoke",
        "livekit":         "agent_os.runtimes.livekit.invoke",
        "terminal":        "agent_os.runtimes.terminal.invoke",
        "hermes_self":     "agent_os.runtimes.hermes_self.invoke",
    }

    if runtime in _ASYNC_RUNTIMES:
        import importlib
        mod = importlib.import_module(_ASYNC_RUNTIMES[runtime])
        return await mod.run(job)

    if runtime in _SYNC_RUNTIMES:
        import importlib
        mod = importlib.import_module(_SYNC_RUNTIMES[runtime])
        return await asyncio.to_thread(mod.invoke, job)

    raise ValueError(f"Unknown runtime: {runtime}")
