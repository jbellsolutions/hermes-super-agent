"""Stream: hermes — Pull NousResearch/hermes-agent upstream, smoke boot+slack+memory+skills."""
from __future__ import annotations

from agent_os.upgrader.smoke.hermes import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/hermes-agent", smoke)
