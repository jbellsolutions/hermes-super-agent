"""Karpathy autoresearch loop. Evolves prompts against binary assertions."""
from __future__ import annotations


def research(skill_path: str, n_variations: int = 5) -> dict:
    """Generate prompt variations, score against assertions, promote the winner.

    TODO(stage-4 + stage-5): wire DSPy + vendor/agi-1.
    Promotion bar: winner > incumbent by >=5pp on confidence-adjusted score.
    """
    return {
        "status": "stub",
        "skill_path": skill_path,
        "n_variations": n_variations,
        "winner": None,
        "promoted": False,
        "todo": "wire DSPy + agi-1 /agi-research",
    }
