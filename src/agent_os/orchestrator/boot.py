"""Boot guidance for the Hermes orchestrator with Super Agent config."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()
DEFAULT_IDENTITY = os.environ.get("HERMES_PROFILE", "supersan")


def _hermes_version() -> str | None:
    hermes = shutil.which("hermes")
    if not hermes:
        return None
    try:
        result = subprocess.run(
            [hermes, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return "installed (version check failed)"
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else "installed"


def boot_hermes(identity: str = DEFAULT_IDENTITY) -> dict[str, Any]:
    """Return launch guidance for the current Super Agent stage.

    The public `agent-os boot` command is still a scaffold diagnostic. It should
    not pretend to start a live Hermes session. A real operator should start
    Hermes directly with `hermes` after `hermes setup` / `hermes doctor` pass.
    """
    identity_path = (
        Path(__file__).parent / "config" / "identities" / f"{identity}.yaml"
    )
    version = _hermes_version()
    if version:
        return {
            "status": "scaffold_not_error",
            "message": "agent-os boot is a Stage 2 scaffold diagnostic; Hermes itself is installed and should be started with the hermes CLI.",
            "hermes": version,
            "identity": identity,
            "identity_path": str(identity_path),
            "vault_root": str(VAULT_ROOT),
            "stage": "2 (wire Super Agent boot adapter to Hermes)",
            "start_commands": [
                "hermes doctor",
                "hermes",
                "hermes gateway setup  # optional, for Telegram/Slack",
                "hermes gateway run    # optional foreground test",
            ],
            "super_agent_commands": [
                "uv run agent-os manifest",
                "uv run agent-os explain",
                "uv run agent-os route --tags coding",
            ],
            "todo": "wire agent-os boot to configure/start Hermes profiles and channel listeners automatically",
        }
    return {
        "status": "hermes_missing",
        "message": "Hermes Agent is not installed or not on PATH. Install Hermes first, then run hermes setup/doctor.",
        "install_command": "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash",
        "identity": identity,
        "identity_path": str(identity_path),
        "vault_root": str(VAULT_ROOT),
        "stage": "0 (install Hermes)",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(boot_hermes(), indent=2))
