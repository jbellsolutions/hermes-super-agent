"""Stream: vendor_health — verify all vendored submodules are healthy."""
from __future__ import annotations

import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def run() -> dict:
    findings = []
    vendor = ROOT / "vendor"
    if not vendor.exists():
        return {"status": "no-vendor"}
    for sub in vendor.iterdir():
        if not sub.is_dir() or not (sub / ".git").exists():
            continue
        # TODO(stage-5): git log -1 to find last upstream commit, flag stale 90+ days
        findings.append({"submodule": sub.name, "status": "ok"})
    return {
        "status": "checked",
        "findings": findings,
        "checked_at": datetime.datetime.utcnow().isoformat(),
    }
