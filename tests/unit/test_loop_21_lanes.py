"""Loop 21 — three execution lanes are explicit and gated.

The user's mental model:

  Lane A — Ephemeral sub-agent (~90% of jobs)
    "research these 3 startups", "summarize the news", "draft an email"
    → in-process via hermes_self. No new VPS, no new Railway service.

  Lane B — Outsourced fan-out via the existing Coordinator (~8%)
    "do this 100 ways in parallel", "fan out this research"
    → coordinator runtime. Existing Railway service handles N parallel
      calls. No NEW infrastructure spun up.

  Lane C — Permanent superagent / specialist (~2%, never auto-fires)
    "spin up a cold email superagent", "hire a LinkedIn specialist"
    → spawn-superagent or build-specialist tag. Tier 3. Requires YES.
      Plan card prints an explicit "permanent infra" warning with
      recurring cost.

These tests pin the lane boundaries so future refactors can't blur them.
"""
from __future__ import annotations

from agent_os.orchestrator import intent_classifier, plan_card
from agent_os.orchestrator.adapters.job_router import Job, route
from agent_os.orchestrator.tool_planner import plan as plan_fn


# ---------- Lane A: ephemeral / in-process ----------

EPHEMERAL_PROMPTS = [
    "summarize the news on AI safety today",
    "research these 3 startups: Anthropic, OpenAI, Mistral",
    "draft an email to garry@ycombinator.com",
    "what's on my calendar tomorrow",
    "find me 10 articles on durable workflows",
    "explain how Temporal handles workflow recovery",
    "translate this paragraph to Spanish",
    "what does this error message mean",
]


def test_lane_a_ephemeral_prompts_have_no_spawn_tags():
    """Pure natural-language tasks must not auto-spawn anything."""
    for prompt in EPHEMERAL_PROMPTS:
        intent = intent_classifier.classify(prompt)
        spawn_tags = intent.tags & {
            "spawn-superagent", "vps-spawn", "spawn-vps",
            "build-specialist", "archon", "hire", "hire-agent",
        }
        assert not spawn_tags, (
            f"prompt {prompt!r} accidentally got spawn tags {spawn_tags}"
        )


def test_lane_a_default_route_is_hermes_self():
    """Empty-tag jobs route to hermes_self (in-process LLM call)."""
    for prompt in EPHEMERAL_PROMPTS:
        intent = intent_classifier.classify(prompt)
        job = Job(prompt=prompt, tags=set(intent.tags))
        # Empty intent → empty tags → default route.
        if not intent.tags:
            assert route(job) == "hermes_self", \
                f"prompt {prompt!r} routed to {route(job)!r}, expected hermes_self"


def test_lane_a_plan_does_not_flag_permanent_resource():
    job = Job(prompt="summarize the news", tags=set())
    plan = plan_fn(job)
    assert plan.permanent_resource is False
    assert plan.permanent_resource_kind == ""


# ---------- Lane B: outsourced fan-out ----------

FANOUT_PROMPTS = [
    "do this research 100 ways in parallel",
    "fan out this task across 50 sub-agents",
    "run a swarm on these 200 leads",
    "process these 30 variants in parallel",
]


def test_lane_b_fanout_prompts_get_fanout_tag():
    for prompt in FANOUT_PROMPTS:
        intent = intent_classifier.classify(prompt)
        assert "fan-out" in intent.tags, \
            f"prompt {prompt!r} did not get fan-out tag (got {intent.tags})"


def test_lane_b_fanout_routes_to_coordinator_not_spawn():
    """Fan-out routes to the existing coordinator service — no new VPS."""
    job = Job(prompt="do this 50 ways in parallel", tags={"fan-out"})
    assert route(job) == "coordinator"
    # Coordinator is a deployed Railway service, not a VPS spawn.
    assert route(job) not in {"vps_spawn", "a2a_delegate"}


def test_lane_b_fanout_does_not_flag_permanent_resource():
    """Fan-out uses existing infra. No 'permanent infra' warning."""
    job = Job(prompt="fan out this to 100 sub-agents", tags={"fan-out"})
    plan = plan_fn(job)
    assert plan.permanent_resource is False, \
        "fan-out reuses existing Coordinator — no NEW permanent infra"


# ---------- Lane C: permanent spawn ----------

SPAWN_VPS_PROMPTS = [
    "spin up a cold email superagent",
    "spin up a new superagent for me",
    "spawn a new superagent",
    "hire a LinkedIn outreach agent",
    "create a permanent SDR specialist for me",
    "deploy a new permanent agent",
]

BUILD_SPECIALIST_PROMPTS = [
    "build me an SEO specialist that writes blog posts",
    "create me a research specialist who finds investor leads",
    "design me a new specialist",
]


def test_lane_c_spawn_vps_prompts_get_spawn_tag():
    for prompt in SPAWN_VPS_PROMPTS:
        intent = intent_classifier.classify(prompt)
        assert "spawn-superagent" in intent.tags, \
            f"prompt {prompt!r} did not get spawn-superagent (got {intent.tags})"


def test_lane_c_build_specialist_prompts_get_specialist_tag():
    for prompt in BUILD_SPECIALIST_PROMPTS:
        intent = intent_classifier.classify(prompt)
        assert "build-specialist" in intent.tags, \
            f"prompt {prompt!r} did not get build-specialist (got {intent.tags})"


def test_lane_c_spawn_vps_routes_to_vps_spawn():
    job = Job(prompt="spin up a cold email superagent",
              tags={"spawn-superagent"})
    assert route(job) == "vps_spawn"


def test_lane_c_build_specialist_routes_to_a2a_delegate():
    """Archon-built specialists go through a2a_delegate, not vps_spawn."""
    job = Job(prompt="build me an SEO specialist",
              tags={"build-specialist"})
    assert route(job) == "a2a_delegate"


def test_lane_c_spawn_forces_tier_3():
    """Permanent-infra spawns must be Tier 3 with explicit YES required."""
    for tag in ("spawn-superagent", "vps-spawn", "build-specialist",
                "archon", "hire-agent", "permanent-agent"):
        job = Job(prompt="x", tags={tag})
        plan = plan_fn(job)
        assert plan.tier == 3, \
            f"tag {tag!r} produced tier {plan.tier}, expected 3"
        assert plan.requires_explicit_confirm, \
            f"tag {tag!r} did not require explicit confirm"


def test_lane_c_spawn_flags_permanent_resource_kind():
    """ToolPlan.permanent_resource_kind tells the UI which kind of infra."""
    vps_job = Job(prompt="spin up a superagent", tags={"spawn-superagent"})
    vps_plan = plan_fn(vps_job)
    assert vps_plan.permanent_resource is True
    assert vps_plan.permanent_resource_kind == "vps"

    rail_job = Job(prompt="build me an SEO specialist",
                   tags={"build-specialist"})
    rail_plan = plan_fn(rail_job)
    assert rail_plan.permanent_resource is True
    assert rail_plan.permanent_resource_kind == "railway-service"


def test_lane_c_plan_card_shows_permanent_infra_warning():
    """The Tier 3 plan card prints an explicit recurring-cost warning."""
    job = Job(prompt="spin up a cold email superagent",
              tags={"spawn-superagent"})
    plan = plan_fn(job)
    card = plan_card.render_markdown(plan)
    assert "Permanent infra" in card
    assert "recurring" in card.lower()
    assert "vps" in card.lower() or "digitalocean" in card.lower()


def test_lane_c_railway_specialist_card_says_railway():
    job = Job(prompt="build me a research specialist",
              tags={"build-specialist"})
    plan = plan_fn(job)
    card = plan_card.render_markdown(plan)
    assert "Permanent infra" in card
    assert "Railway" in card


# ---------- Cross-lane: outbound channels are still Tier 3, no new infra ----------

def test_outbound_phone_does_not_flag_permanent_resource():
    """Outbound phone uses an existing Retell agent — no new infra spun up."""
    job = Job(prompt="call (555) 123-4567 — pitch the consulting offer",
              tags={"outbound-phone"})
    plan = plan_fn(job)
    assert plan.tier == 3
    assert plan.permanent_resource is False, \
        "outbound phone reuses an existing Retell agent — no NEW permanent infra"


def test_intent_classifier_detects_outbound_phone_from_phone_number():
    intent = intent_classifier.classify("call (555) 123-4567")
    assert "outbound-phone" in intent.tags


def test_intent_classifier_detects_cold_email():
    intent = intent_classifier.classify(
        "send a cold email to garry@ycombinator.com"
    )
    assert "outbound-email" in intent.tags
