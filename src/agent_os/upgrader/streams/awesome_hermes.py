"""Stream: awesome_hermes — Pull community skills as REVIEW-REQUIRED — never auto-promote."""
from __future__ import annotations

from agent_os.upgrader.smoke.awesome_hermes import smoke
from agent_os.upgrader.streams._common import upgrade_submodule


def run() -> dict:
    return upgrade_submodule("vendor/awesome-hermes-agent", smoke)
