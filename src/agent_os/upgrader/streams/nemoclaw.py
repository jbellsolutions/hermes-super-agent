"""Stream: nemoclaw — PARKED until NVIDIA marks GA."""
from __future__ import annotations

import os


def run() -> dict:
    if os.environ.get("UPGRADER_ENABLE_NEMOCLAW", "false").lower() != "true":
        return {
            "status": "parked",
            "reason": "NemoClaw preview; flip UPGRADER_ENABLE_NEMOCLAW=true when GA",
        }
    # TODO(when-ga): import _common.upgrade_submodule and run smoke
    return {"status": "parked-flag-on-but-not-implemented"}
