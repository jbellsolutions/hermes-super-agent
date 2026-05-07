"""Unit tests for the plan card emitter.

Renders a ToolPlan into one of three tiers (banner / card / hard-stop) plus
a fourth blocked-by-identity format.
"""
from __future__ import annotations

import json

from agent_os.orchestrator import plan_card
from agent_os.orchestrator.tool_planner import Alternative, ToolPlan


def _plan(**overrides) -> ToolPlan:
    base = dict(
        task_summary="research the AI agent market",
        primary_tool="openswarm",
        primary_reason="router→openswarm",
        alternatives=[
            Alternative(name="hermes_self", score=20, reason="fallback"),
            Alternative(name="openclaw", score=12, reason="grind"),
        ],
        tier=2,
        tier_reason="mutates state OR substantive work",
        estimated_cost_usd=0.40,
        estimated_seconds=600,
        risk_class="low",
        grace_seconds=3,
        requires_explicit_confirm=False,
        model_recommendation="claude-opus-4.7",
        model_reason="preferred + matches task class 'deliverable_production'",
        bundle_used="primary_hermes",
        blocked_reason=None,
        signals=["mutation:write", "cost:$0.40"],
    )
    base.update(overrides)
    return ToolPlan(**base)


# --------------------------------------------------------------------------
# tier 1 banner
# --------------------------------------------------------------------------

def test_tier_1_banner_one_line():
    out = plan_card.render(_plan(tier=1, grace_seconds=0))
    assert out.startswith("⚡")
    assert out.count("\n") == 0
    assert "openswarm" in out


def test_tier_1_includes_model():
    out = plan_card.render(_plan(tier=1, grace_seconds=0))
    assert "claude-opus-4.7" in out


# --------------------------------------------------------------------------
# tier 2 card
# --------------------------------------------------------------------------

def test_tier_2_card_four_lines():
    out = plan_card.render(_plan(tier=2))
    lines = out.splitlines()
    assert len(lines) == 4
    assert lines[0].startswith("📋 Plan:")
    assert "Tools:" in lines[1]
    assert "Model:" in lines[2]
    assert "Tier 2" in lines[3]


def test_tier_2_shows_alternatives():
    out = plan_card.render(_plan(tier=2))
    assert "hermes_self" in out
    assert "openclaw" in out


def test_tier_2_prompts_for_explicit_yes():
    """Tier 2 must ask for an explicit 'yes' — channels can't auto-proceed
    after a grace window because Telegram replies are async and might not
    land before grace_seconds elapses (F4: align card text with bot logic)."""
    out = plan_card.render(_plan(tier=2, grace_seconds=3))
    assert "yes" in out.lower()
    assert "proceeding in" not in out


def test_tier_2_lists_overrides():
    out = plan_card.render(_plan(tier=2))
    assert "/cancel" in out
    assert "/use" in out
    assert "/why" in out


# --------------------------------------------------------------------------
# tier 3 hard stop
# --------------------------------------------------------------------------

def test_tier_3_hard_stop_format():
    out = plan_card.render(_plan(
        tier=3, grace_seconds=0, requires_explicit_confirm=True,
        risk_class="high", estimated_cost_usd=0.60,
        task_summary="deploy main to production",
    ))
    assert out.startswith("🛑")
    assert "Tier 3" in out
    assert "YES" in out
    assert "destructive" in out


def test_tier_3_high_cost_flavor():
    out = plan_card.render(_plan(
        tier=3, grace_seconds=0, requires_explicit_confirm=True,
        risk_class="low", estimated_cost_usd=2.50,
    ))
    assert "expensive" in out


def test_tier_3_default_flavor():
    out = plan_card.render(_plan(
        tier=3, grace_seconds=0, requires_explicit_confirm=True,
        risk_class="low", estimated_cost_usd=0.40,
    ))
    assert "high-impact" in out


# --------------------------------------------------------------------------
# blocked-by-identity
# --------------------------------------------------------------------------

def test_blocked_renders_hint():
    out = plan_card.render(_plan(
        tier=3, blocked_reason="identity 'coo' has default_tier_ceiling=2",
    ))
    assert out.startswith("🚫")
    assert "Blocked" in out
    assert "coo" in out


# --------------------------------------------------------------------------
# json channel
# --------------------------------------------------------------------------

def test_json_channel_returns_valid_json():
    out = plan_card.render(_plan(), channel="json")
    parsed = json.loads(out)
    assert parsed["primary_tool"] == "openswarm"
    assert parsed["tier"] == 2
    assert parsed["model_recommendation"] == "claude-opus-4.7"
    assert isinstance(parsed["alternatives"], list)
    assert parsed["alternatives"][0]["name"] == "hermes_self"


def test_json_includes_signals():
    out = plan_card.render(_plan(), channel="json")
    parsed = json.loads(out)
    assert parsed["signals"] == ["mutation:write", "cost:$0.40"]


# --------------------------------------------------------------------------
# why channel
# --------------------------------------------------------------------------

def test_why_renders_explanation():
    out = plan_card.render(_plan(), channel="why")
    assert out.startswith("📌 Why this plan")
    assert "Picked: openswarm" in out
    assert "Tier: 2" in out
    assert "Other candidates" in out
    assert "claude-opus-4.7" in out


def test_why_omits_alternatives_when_none():
    out = plan_card.render(_plan(alternatives=[]), channel="why")
    assert "Other candidates" not in out


# --------------------------------------------------------------------------
# default channel
# --------------------------------------------------------------------------

def test_default_channel_is_markdown():
    a = plan_card.render(_plan())
    b = plan_card.render(_plan(), channel="markdown")
    assert a == b


def test_unknown_channel_falls_back_to_markdown():
    out = plan_card.render(_plan(), channel="totally_unknown")
    assert out.startswith("📋")  # tier 2 banner
