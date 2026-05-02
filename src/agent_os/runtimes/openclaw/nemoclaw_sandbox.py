"""Optional NVIDIA NemoClaw sandbox wrapping OpenClaw."""
from __future__ import annotations

import os


def is_enabled() -> bool:
    return os.environ.get("UPGRADER_ENABLE_NEMOCLAW", "false").lower() == "true"


def wrap_invoke(invoke_fn):
    """TODO(when-ga): wrap OpenClaw invoke in NemoClaw OpenShell sandbox."""
    if not is_enabled():
        return invoke_fn
    raise NotImplementedError("NemoClaw GA flag flipped but wrapper not yet implemented")
