"""Smoke test for OpenSwarm upgrade.

Runs in this order, returning False on the first failure:

  1. Vendor structural sanity — required files still present in vendor/openswarm.
  2. Per-swarm sanity — each registered fleet member has folder, manifest,
     vault skill, AND its recorded customization replays cleanly against the
     fresh vendor (catches "upstream changed in a way that breaks our
     customization").

This is a no-LLM check — it does NOT boot servers. The HealthValidator path
is reserved for the manual re-promotion flow; running 50 swarms' health checks
nightly is not what we want.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from agent_os.runtimes.openswarm import customizers, fleet, registry, skills

REQUIRED_VENDOR_FILES = (
    "swarm.py",
    "server.py",
    "AGENTS.md",
)


def smoke() -> bool:
    try:
        if not _vendor_structural_sanity():
            return False
        return _all_swarms_replay_clean()
    except Exception:  # noqa: BLE001 — smoke must never raise
        return False


def _vendor_structural_sanity() -> bool:
    try:
        vendor = fleet.vendor_root()
    except RuntimeError:
        return False
    for required in REQUIRED_VENDOR_FILES:
        if not (vendor / required).exists():
            return False
    return True


def _all_swarms_replay_clean() -> bool:
    swarms = registry.list_all()
    if not swarms:
        # Empty fleet is fine — vendor sanity already passed.
        return True

    for name, entry in swarms.items():
        if not _swarm_state_present(name, entry):
            return False
        # Default swarm has no recorded customization to replay.
        if name == "default":
            continue
        if not _replay_clean(name, entry):
            return False
    return True


def _swarm_state_present(name: str, entry: dict[str, Any]) -> bool:
    folder = fleet.folder_for(name)
    if not folder.exists():
        return False
    if not (folder / "swarm.py").exists():
        return False
    skill_path = skills.ACTIVE_DIR / f"{name}-swarm.md"
    if not skill_path.exists():
        return False
    return True


def _replay_clean(name: str, entry: dict[str, Any]) -> bool:
    """Re-run the recorded customizer against a fresh vendor clone in /tmp.

    Returns True iff the customizer reports success.
    """
    cust_name = entry.get("customizer") or "noop"
    if cust_name == "noop":
        return True  # nothing to replay
    try:
        vendor = fleet.vendor_root()
    except RuntimeError:
        return False
    with tempfile.TemporaryDirectory() as td:
        staging = Path(td) / name
        try:
            shutil.copytree(vendor, staging, ignore=shutil.ignore_patterns(".git"))
        except OSError:
            return False
        agents_md_path = staging / "AGENTS.md"
        agents_md = agents_md_path.read_text() if agents_md_path.exists() else ""
        ctx = customizers.BuildContext(
            name=name,
            description=entry.get("build_prompt") or entry.get("business_purpose") or "",
            swarm_dir=staging,
            agents_md=agents_md,
        )
        try:
            cust = customizers.get_customizer(
                cust_name, options=entry.get("customizer_options") or {}
            )
        except (ValueError, TypeError):
            return False
        outcome = cust.customize(ctx)
        return bool(outcome.success)
