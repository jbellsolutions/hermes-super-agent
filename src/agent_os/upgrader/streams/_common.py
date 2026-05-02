"""Shared upgrade logic: git submodule update, smoke run, promote-or-quarantine."""
from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd or ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def upgrade_submodule(submodule_path: str, smoke_fn: Callable[[], bool]) -> dict:
    """Pull upstream, run smoke, promote if green, quarantine if red."""
    sub = ROOT / submodule_path
    if not sub.exists():
        return {"status": "skip", "reason": f"submodule {submodule_path} not initialized"}
    before = git("rev-parse", "HEAD", cwd=sub)
    git("fetch", "origin", cwd=sub)
    after = git("rev-parse", "origin/HEAD", cwd=sub)
    if before == after:
        return {"status": "no-upgrade", "head": before}
    git("checkout", "origin/HEAD", cwd=sub)
    try:
        ok = smoke_fn()
    except Exception as e:
        ok = False
        smoke_err = str(e)
    else:
        smoke_err = None
    if ok:
        git("checkout", "-B", "main", cwd=sub)
        return {"status": "promoted", "from": before, "to": after}
    git("checkout", before, cwd=sub)
    return {"status": "quarantined", "from": before, "attempted": after, "error": smoke_err}
