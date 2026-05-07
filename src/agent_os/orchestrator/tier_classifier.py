"""Tier classification — decides whether a job is autonomous (1), plan-card+grace (2),
or hard-stop (3) based on tags + cost + time.

Rules live in ``config/tiers.yaml`` so they're tunable without code changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from agent_os.orchestrator.adapters.job_router import Job


def _config_path() -> Path:
    return Path(__file__).with_name("config") / "tiers.yaml"


def load_rules(path: Path | None = None) -> dict[str, Any]:
    p = path or _config_path()
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}


@dataclass
class TierDecision:
    tier: int
    reason: str
    matched_rule: str | None = None
    signals: list[str] = field(default_factory=list)


# Sentinels for tag-pair matching — tuples can't go in sets directly.
def _tag_pair_match(tags: set[str], pair: list[str]) -> bool:
    return all(p.lower() in tags for p in pair)


def classify(
    job: Job,
    *,
    cost_usd: float | None = None,
    estimated_minutes: float | None = None,
    rules: dict[str, Any] | None = None,
) -> TierDecision:
    """Classify a job into tier 1/2/3.

    Pure: no I/O, no side effects. Signals are captured in the result so the
    plan card can show 'why this tier'.
    """
    rules = rules if rules is not None else load_rules()
    tags = {tag.lower() for tag in job.tags}
    cost = float(cost_usd or 0.0)
    minutes = float(
        estimated_minutes
        if estimated_minutes is not None
        else (job.estimated_minutes or 0)
    )
    signals: list[str] = []

    # ---- Tier 3 first (hard stops) ----
    t3_tags = set(rules.get("tier_3_tags", []))
    matched_t3 = tags & t3_tags
    if matched_t3:
        return TierDecision(
            tier=3,
            reason=f"tag match: {sorted(matched_t3)[0]}",
            matched_rule="tier_3_tags",
            signals=[f"tag:{t}" for t in sorted(matched_t3)],
        )
    for pair in rules.get("tier_3_pairs", []):
        if _tag_pair_match(tags, pair):
            return TierDecision(
                tier=3,
                reason=f"pair match: {pair}",
                matched_rule="tier_3_pairs",
                signals=[f"pair:{'+'.join(pair)}"],
            )
    if cost > rules.get("tier_3_cost_threshold_usd", 1.00):
        return TierDecision(
            tier=3,
            reason=f"cost ${cost:.2f} > threshold",
            matched_rule="tier_3_cost_threshold_usd",
            signals=[f"cost:${cost:.2f}"],
        )
    if minutes >= rules.get("tier_3_estimated_minutes", 60):
        return TierDecision(
            tier=3,
            reason=f"estimated {minutes:.0f}min >= threshold",
            matched_rule="tier_3_estimated_minutes",
            signals=[f"minutes:{minutes:.0f}"],
        )

    # ---- Tier 1 next (cheap, read-only) ----
    t1_tags = set(rules.get("tier_1_tags", []))
    matched_t1 = tags & t1_tags
    mutation_tags = set(rules.get("mutation_tags", []))
    has_mutation = bool(tags & mutation_tags)

    if matched_t1 and not has_mutation:
        signals.extend(f"tag:{t}" for t in sorted(matched_t1))
        return TierDecision(
            tier=1,
            reason=f"read-only tag: {sorted(matched_t1)[0]}",
            matched_rule="tier_1_tags",
            signals=signals,
        )
    if (
        cost < rules.get("tier_1_cost_threshold_usd", 0.05)
        and not has_mutation
        and minutes < rules.get("tier_2_estimated_minutes", 5)
    ):
        return TierDecision(
            tier=1,
            reason=f"cheap (${cost:.2f}) + idempotent + fast",
            matched_rule="default_tier_1",
            signals=[f"cost:${cost:.2f}", f"minutes:{minutes:.1f}"],
        )

    # ---- Tier 2 default ----
    if has_mutation:
        signals.append(f"mutation:{sorted(tags & mutation_tags)[0]}")
    if cost >= rules.get("tier_2_cost_threshold_usd", 0.05):
        signals.append(f"cost:${cost:.2f}")
    if minutes >= rules.get("tier_2_estimated_minutes", 5):
        signals.append(f"minutes:{minutes:.0f}")
    return TierDecision(
        tier=2,
        reason="mutates state OR substantive work",
        matched_rule="default_tier_2",
        signals=signals or ["default"],
    )
