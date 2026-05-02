"""Stream: codex — package upgrade for openai/codex CLI."""
from __future__ import annotations

import subprocess

from agent_os.upgrader.smoke.codex import smoke


def run() -> dict:
    """Upgrade Codex CLI via npm/pip. Smoke before promoting."""
    # TODO(stage-5): pin path. For now, soft-attempt and don't fail the daemon.
    try:
        before = subprocess.run(
            ["codex", "--version"], capture_output=True, text=True
        ).stdout.strip()
    except FileNotFoundError:
        return {"status": "skip", "reason": "codex CLI not installed"}
    subprocess.run(["npm", "install", "-g", "@openai/codex"], capture_output=True, check=False)
    after = subprocess.run(
        ["codex", "--version"], capture_output=True, text=True
    ).stdout.strip()
    if before == after:
        return {"status": "no-upgrade", "version": before}
    if smoke():
        return {"status": "promoted", "from": before, "to": after}
    return {"status": "quarantined", "from": before, "attempted": after}
