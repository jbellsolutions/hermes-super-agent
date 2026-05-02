"""Stream: agi1 — Pull jbellsolutions/agi-1, smoke audit+council+research+genome."""
from __future__ import annotations

from agent_os.upgrader.smoke.agi1 import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/agi-1", smoke)
