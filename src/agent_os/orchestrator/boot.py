"""Boot the Hermes orchestrator with our config and adapters."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()
DEFAULT_IDENTITY = "coo"


def boot_hermes(identity: str = DEFAULT_IDENTITY) -> dict[str, Any]:
    """Start Hermes with our identity config + vault-memory adapter + Slack listener.

    TODO(stage-2): wire vendor/hermes-agent here. The function below currently
    returns a stub describing the boot intent; replace with real Hermes startup.
    """
    identity_path = (
        Path(__file__).parent / "config" / "identities" / f"{identity}.yaml"
    )
    return {
        "status": "stub",
        "identity": identity,
        "identity_path": str(identity_path),
        "vault_root": str(VAULT_ROOT),
        "stage": "2 (boot Hermes)",
        "todo": "import vendor/hermes-agent + apply config + start Slack/Telegram listeners",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(boot_hermes(), indent=2))
