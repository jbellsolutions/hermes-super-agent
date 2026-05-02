"""Stream: openclaw — Pull openclaw/openclaw upstream, smoke shell+browser+output round-trip."""
from __future__ import annotations

from agent_os.upgrader.smoke.openclaw import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/openclaw", smoke)
