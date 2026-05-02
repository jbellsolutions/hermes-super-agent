"""Stream: browser_use.

Pull browser-use/browser-use upstream and smoke nav/extract/screenshot/fallback.
"""
from __future__ import annotations

from agent_os.upgrader.smoke.browser_use import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/browser-use", smoke)
