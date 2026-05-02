"""Nightly cron entry point. Runs all 10 streams in sequence."""
from __future__ import annotations

import datetime
import os
from pathlib import Path

import yaml

from agent_os.upgrader.streams import (
    agi1,
    aider,
    awesome_hermes,
    browser_use,
    codex,
    hermes,
    mcp_registry,
    nemoclaw,
    openclaw,
    vendor_health,
)

VAULT_UPGRADES = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve() / "upgrades"

STREAMS = [
    ("hermes", hermes.run),
    ("openclaw", openclaw.run),
    ("browser_use", browser_use.run),
    ("aider", aider.run),
    ("codex", codex.run),
    ("agi1", agi1.run),
    ("awesome_hermes", awesome_hermes.run),
    ("nemoclaw", nemoclaw.run),  # parked — early-return until UPGRADER_ENABLE_NEMOCLAW=true
    ("mcp_registry", mcp_registry.run),
    ("vendor_health", vendor_health.run),
]


def run_nightly() -> dict:
    today = datetime.date.today().isoformat()
    results = {}
    for name, runner in STREAMS:
        try:
            results[name] = runner()
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    log = {"date": today, "results": results}
    VAULT_UPGRADES.mkdir(parents=True, exist_ok=True)
    (VAULT_UPGRADES / f"{today}.yaml").write_text(yaml.safe_dump(log, sort_keys=False))
    return log


if __name__ == "__main__":
    import json
    print(json.dumps(run_nightly(), indent=2))
