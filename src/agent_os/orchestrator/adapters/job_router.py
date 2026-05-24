"""Decide which runtime handles a given job, based on tags."""
from __future__ import annotations

import os
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
    "local_spawn",       # Kaioken — spawn a Tier 2 superagent as a local Docker container
    "coordinator",       # fan-out to N-agent swarm via deployed A2A service (model-pluggable)
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
    # Coordinator: N-agent fan-out via A2A service, Temporal-wrapped, model-pluggable.
    if "fan-out" in t or "coordinator" in t or "swarm-coordinator" in t:
        return "coordinator"
    # Superagent spawning — full Hermes + orchestrator. In Kaioken mode the
    # spawn lands in a local Docker container; in Super-Saiyan-5 mode it's a
    # real DigitalOcean droplet. Same A2A contract on both ends.
    if "spawn-superagent" in t or "vps-spawn" in t:
        if os.getenv("HERMES_MODE", "").lower() == "kaioken":
            return "local_spawn"
        return "vps_spawn"
    # Archon agent builder — delegates "create a specialist" to Archon A2A endpoint.
    if "build-specialist" in t or "archon" in t:
        return "a2a_delegate"
    # COO outbound channel — phone (Retell) and email (Instantly) share one runtime.
    if t & {"phone", "retell", "outbound-phone",
            "email", "outbound-email", "cold-email", "instantly"}:
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


_ASYNC_RUNTIMES = {
    "coordinator":      "agent_os.runtimes.coordinator.invoke",
    "retell_channel":   "agent_os.runtimes.retell_channel.invoke",
    "vps_spawn":        "agent_os.runtimes.vps_spawn.invoke",
    "local_spawn":      "agent_os.runtimes.local_spawn.invoke",
    "a2a_delegate":     "agent_os.runtimes.a2a_delegate.invoke",
}

# Fabric runtimes are intent-driven: when the user (or upstream classifier)
# explicitly tags a job `spawn-superagent`, `fan-out`, etc., that is an
# instruction about WHICH LANE to take — not a tool preference the planner
# is allowed to second-guess. dispatch() prefers tag-routing over
# plan.primary_tool when route() lands on one of these.
_FABRIC_RUNTIMES = frozenset({
    "coordinator", "vps_spawn", "local_spawn", "a2a_delegate", "retell_channel",
})
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

KNOWN_RUNTIMES: set[str] = set(_ASYNC_RUNTIMES) | set(_SYNC_RUNTIMES)


async def dispatch(job: Job, plan=None):
    """Route job → correct runtime module → call run(job).

    If `plan` (a ToolPlan from tool_planner) is provided, its `primary_tool`
    overrides tag-based routing when the tool name maps to a known runtime,
    and its `model_recommendation` is propagated into job.metadata['model']
    so the runtime LLM call honors the planner's model choice.

    All fabric runtimes (coordinator, retell_channel, vps_spawn,
    a2a_delegate) expose `async def run(job)`. Legacy runtimes that only
    have a sync `invoke(job)` are wrapped with asyncio.to_thread.
    """
    import asyncio

    # Always compute tag-based route first — for fabric runtimes (spawn,
    # fan-out, delegate, retell), tag intent OVERRIDES any planner choice.
    # The planner scores skills/tools; it doesn't know that the user
    # explicitly asked to spawn a superagent rather than do research.
    tag_route = route(job)

    runtime = None
    if plan is not None:
        rec = getattr(plan, "model_recommendation", None)
        if rec and not job.metadata.get("model"):
            job.metadata["model"] = rec

        primary = getattr(plan, "primary_tool", None)
        if tag_route in _FABRIC_RUNTIMES:
            # Spawn/fan-out/delegate jobs: tag intent wins. The plan card's
            # model recommendation is still honored above.
            runtime = tag_route
        elif primary and primary in KNOWN_RUNTIMES:
            runtime = primary

    if runtime is None:
        runtime = tag_route

    if runtime in _ASYNC_RUNTIMES:
        import importlib
        mod = importlib.import_module(_ASYNC_RUNTIMES[runtime])
        return await mod.run(job)

    if runtime in _SYNC_RUNTIMES:
        import importlib
        mod = importlib.import_module(_SYNC_RUNTIMES[runtime])
        return await asyncio.to_thread(mod.invoke, job)

    raise ValueError(f"Unknown runtime: {runtime}")
