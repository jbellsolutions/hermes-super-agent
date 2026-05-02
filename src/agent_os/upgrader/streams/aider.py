"""Stream: aider — Pull Aider-AI/aider upstream, smoke fixture-edit+test+commit-format."""
from __future__ import annotations

from agent_os.upgrader.smoke.aider import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/aider", smoke)
