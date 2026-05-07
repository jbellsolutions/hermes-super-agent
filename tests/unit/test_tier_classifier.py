"""Unit tests for the tier classifier.

The classifier puts each Job into Tier 1 (autonomous + banner), Tier 2
(plan card + 3s grace), or Tier 3 (hard stop). Rules are loaded from
``config/tiers.yaml`` and are tunable.
"""
from __future__ import annotations

import pytest

from agent_os.orchestrator import tier_classifier
from agent_os.orchestrator.adapters.job_router import Job


@pytest.fixture(scope="module")
def rules() -> dict:
    return tier_classifier.load_rules()


# --------------------------------------------------------------------------
# Tier 3 — hard stops
# --------------------------------------------------------------------------

@pytest.mark.parametrize("tag", [
    "deploy", "delete", "destroy", "force-push", "publish",
    "send-email", "drop-table", "merge-main", "rm-rf",
])
def test_tier_3_destructive_tags(rules, tag):
    job = Job(prompt="...", tags={tag})
    decision = tier_classifier.classify(job, rules=rules)
    assert decision.tier == 3
    assert decision.matched_rule == "tier_3_tags"
    assert any(s.startswith("tag:") for s in decision.signals)


def test_tier_3_pair_production_write(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"production", "write"}), rules=rules,
    )
    assert decision.tier == 3
    assert decision.matched_rule == "tier_3_pairs"


def test_tier_3_pair_main_force_push(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"main", "force-push"}), rules=rules,
    )
    assert decision.tier == 3


def test_tier_3_high_cost(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"build"}), cost_usd=2.50, rules=rules,
    )
    assert decision.tier == 3
    assert decision.matched_rule == "tier_3_cost_threshold_usd"


def test_tier_3_long_running(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"build"}), estimated_minutes=120, rules=rules,
    )
    assert decision.tier == 3
    assert decision.matched_rule == "tier_3_estimated_minutes"


# --------------------------------------------------------------------------
# Tier 1 — read-only
# --------------------------------------------------------------------------

@pytest.mark.parametrize("tag", [
    "read", "search", "explain", "status", "list", "route", "lookup",
])
def test_tier_1_read_only_tags(rules, tag):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={tag}), rules=rules,
    )
    assert decision.tier == 1


def test_tier_1_cheap_idempotent_default(rules):
    """No tags + zero cost + no minutes → Tier 1 by default."""
    decision = tier_classifier.classify(
        Job(prompt="hello"), cost_usd=0.0, estimated_minutes=0, rules=rules,
    )
    assert decision.tier == 1


def test_tier_1_blocked_when_mutation_tag_present(rules):
    """A read-only tag + a mutation tag should NOT collapse to tier 1."""
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"read", "write"}), rules=rules,
    )
    # mutation lifts it to tier 2
    assert decision.tier == 2


# --------------------------------------------------------------------------
# Tier 2 — default
# --------------------------------------------------------------------------

def test_tier_2_mutation_tag(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"write"}), rules=rules,
    )
    assert decision.tier == 2
    assert any(s.startswith("mutation:") for s in decision.signals)


def test_tier_2_substantive_cost(rules):
    decision = tier_classifier.classify(
        Job(prompt="..."), cost_usd=0.40, rules=rules,
    )
    assert decision.tier == 2


def test_tier_2_substantive_minutes(rules):
    decision = tier_classifier.classify(
        Job(prompt="..."), estimated_minutes=10, rules=rules,
    )
    assert decision.tier == 2


# --------------------------------------------------------------------------
# Determinism + signals
# --------------------------------------------------------------------------

def test_classify_is_deterministic(rules):
    job = Job(prompt="ship to prod", tags={"deploy", "production"})
    a = tier_classifier.classify(job, rules=rules)
    b = tier_classifier.classify(job, rules=rules)
    assert (a.tier, a.matched_rule) == (b.tier, b.matched_rule)


def test_signals_populated(rules):
    decision = tier_classifier.classify(
        Job(prompt="...", tags={"deploy"}), rules=rules,
    )
    assert decision.signals
    assert any("deploy" in s for s in decision.signals)


def test_load_rules_returns_dict():
    rules = tier_classifier.load_rules()
    assert isinstance(rules, dict)
    # core fields the classifier expects
    assert "tier_3_tags" in rules
    assert "tier_1_tags" in rules
    assert "mutation_tags" in rules
