"""Unit tests for the tool planner.

Covers scoring, identity-bundle filtering, ceiling enforcement, and the
shape of the returned ToolPlan.
"""
from __future__ import annotations

import pytest

from agent_os.orchestrator import catalog as catalog_mod
from agent_os.orchestrator import tool_planner
from agent_os.orchestrator.adapters.job_router import Job


@pytest.fixture(scope="module")
def cat() -> dict:
    return catalog_mod.build_catalog()


# --------------------------------------------------------------------------
# basic shape
# --------------------------------------------------------------------------

def test_plan_returns_tool_plan(cat):
    plan = tool_planner.plan(
        Job(prompt="hello world"), identity="primary_hermes", catalog=cat,
    )
    assert isinstance(plan, tool_planner.ToolPlan)
    assert plan.primary_tool
    assert plan.task_summary
    assert plan.tier in (1, 2, 3)


def test_task_summary_is_truncated(cat):
    long = "x" * 500
    plan = tool_planner.plan(
        Job(prompt=long), identity="primary_hermes", catalog=cat,
    )
    assert len(plan.task_summary) <= 80


# --------------------------------------------------------------------------
# routing — tag-based picks
# --------------------------------------------------------------------------

def test_multi_deliverable_routes_to_openswarm(cat):
    plan = tool_planner.plan(
        Job(prompt="make me an investor deck", tags={"multi-deliverable"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "openswarm"
    assert plan.tier == 2


def test_pitch_deck_routes_to_openswarm(cat):
    plan = tool_planner.plan(
        Job(prompt="make a deck", tags={"investor-pitch"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "openswarm"


def test_browser_routes_to_browser_use(cat):
    plan = tool_planner.plan(
        Job(prompt="scrape some pages", tags={"browser", "structured"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "browser_use"


def test_voice_routes_to_livekit(cat):
    plan = tool_planner.plan(
        Job(prompt="talk to me", tags={"voice", "realtime"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "livekit"


def test_search_articles_routes_to_exa(cat):
    plan = tool_planner.plan(
        Job(prompt="find some articles", tags={"search", "articles"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "exa"


def test_unknown_tags_fall_back_to_hermes_self(cat):
    plan = tool_planner.plan(
        Job(prompt="just chat with me about strategy"),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.primary_tool == "hermes_self"


# --------------------------------------------------------------------------
# alternatives
# --------------------------------------------------------------------------

def test_alternatives_present_for_routed_pick(cat):
    plan = tool_planner.plan(
        Job(prompt="make a deck", tags={"multi-deliverable"}),
        identity="primary_hermes", catalog=cat,
    )
    # The primary tool is excluded from alternatives.
    assert plan.primary_tool not in {a.name for a in plan.alternatives}


def test_alternatives_sorted_by_score_desc(cat):
    plan = tool_planner.plan(
        Job(prompt="make a deck", tags={"multi-deliverable"}),
        identity="primary_hermes", catalog=cat,
    )
    if len(plan.alternatives) >= 2:
        scores = [a.score for a in plan.alternatives]
        assert scores == sorted(scores, reverse=True)


# --------------------------------------------------------------------------
# identity ceilings + bundle filtering
# --------------------------------------------------------------------------

def test_coo_blocked_for_tier_3_deploy(cat):
    plan = tool_planner.plan(
        Job(prompt="ship to prod", tags={"deploy", "production"}),
        identity="coo", catalog=cat,
    )
    assert plan.tier == 3
    assert plan.blocked_reason is not None
    assert "primary_hermes" in plan.blocked_reason
    assert "coo" in plan.blocked_reason


def test_coo_can_run_tier_2_deck(cat):
    plan = tool_planner.plan(
        Job(prompt="build me a client deck", tags={"multi-deliverable"}),
        identity="coo", catalog=cat,
    )
    assert plan.tier == 2
    assert plan.blocked_reason is None


def test_primary_hermes_no_ceiling(cat):
    plan = tool_planner.plan(
        Job(prompt="ship to prod", tags={"deploy", "production"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.tier == 3
    # primary_hermes never gets blocked.
    assert plan.blocked_reason is None


def test_bundle_used_recorded(cat):
    plan = tool_planner.plan(
        Job(prompt="ping"), identity="coo", catalog=cat,
    )
    assert plan.bundle_used == "coo"


# --------------------------------------------------------------------------
# tier-driven plan card flags
# --------------------------------------------------------------------------

def test_tier_2_has_grace_window(cat):
    plan = tool_planner.plan(
        Job(prompt="build a deck", tags={"multi-deliverable"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.tier == 2
    assert plan.grace_seconds == 3
    assert plan.requires_explicit_confirm is False


def test_tier_3_requires_confirm(cat):
    plan = tool_planner.plan(
        Job(prompt="deploy", tags={"deploy", "production"}),
        identity="primary_hermes", catalog=cat,
    )
    assert plan.tier == 3
    assert plan.requires_explicit_confirm is True
    assert plan.grace_seconds == 0


# --------------------------------------------------------------------------
# cost / time estimates
# --------------------------------------------------------------------------

def test_cost_estimate_from_class():
    assert tool_planner._estimate_cost("low") == 0.05
    assert tool_planner._estimate_cost("medium") == 0.40
    assert tool_planner._estimate_cost("high") == 2.50
    assert tool_planner._estimate_cost(None) == 0.05


def test_seconds_estimate_t3_floors_at_hour():
    assert tool_planner._estimate_seconds("low", 3) >= 3600


def test_summarize_short_passthrough():
    assert tool_planner._summarize("short prompt") == "short prompt"


def test_summarize_long_truncated():
    out = tool_planner._summarize("x" * 200, max_chars=20)
    assert len(out) <= 20
    assert out.endswith("…")


# --------------------------------------------------------------------------
# bundle filter helper
# --------------------------------------------------------------------------

def test_filter_by_bundle_allowed_only():
    tools = {"a": {}, "b": {}, "c": {}}
    bundle = {"tools_allowed": ["a", "b"]}
    out = tool_planner._filter_by_bundle(tools, bundle)
    assert set(out.keys()) == {"a", "b"}


def test_filter_by_bundle_denied_subtracted():
    tools = {"a": {}, "b": {}, "c": {}}
    bundle = {"tools_denied": ["b"]}
    out = tool_planner._filter_by_bundle(tools, bundle)
    assert set(out.keys()) == {"a", "c"}


def test_filter_by_bundle_allowed_minus_denied():
    tools = {"a": {}, "b": {}, "c": {}}
    bundle = {"tools_allowed": ["a", "b"], "tools_denied": ["b"]}
    out = tool_planner._filter_by_bundle(tools, bundle)
    assert set(out.keys()) == {"a"}
