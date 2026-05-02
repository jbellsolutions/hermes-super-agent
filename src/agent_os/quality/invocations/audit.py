"""Wrapper around vendor/agi-1's /agi-audit skill."""
from __future__ import annotations

from pathlib import Path


def audit(target: str | Path) -> dict:
    """Score `target` (a repo, a vault outputs dir, or a single artifact).

    TODO(stage-4): shell out to vendor/agi-1's /agi-audit or import directly.
    Returns: {"score": int, "g_stack": int, "ai_readiness": int, "findings": [...]}
    """
    return {
        "status": "stub",
        "target": str(target),
        "score": None,
        "todo": "wire vendor/agi-1 /agi-audit",
    }
