"""Wrapper around vendor/agi-1's /agi-council 3-agent deliberation."""
from __future__ import annotations


def council(question: str, persona: str | None = None) -> dict:
    """Run a 3-agent council on `question`. Optional persona presets the council.

    TODO(stage-4): wire vendor/agi-1's council engine.
    """
    return {
        "status": "stub",
        "question": question,
        "persona": persona,
        "rounds": [],
        "verdict": None,
        "todo": "wire vendor/agi-1 /agi-council",
    }
