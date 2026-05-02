"""Decide which runtime handles a given job, based on tags."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RuntimeName = Literal[
    "hermes_self",       # default — Hermes handles it itself with sub-agents
    "openclaw",          # autonomous-grind, shell, file-ops
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
