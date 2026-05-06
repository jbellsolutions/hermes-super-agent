"""Stream: openswarm — Pull VRSEN/OpenSwarm upstream, smoke vendor + each
registered fleet member."""
from __future__ import annotations

from agent_os.upgrader.smoke.openswarm import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/openswarm", smoke)
