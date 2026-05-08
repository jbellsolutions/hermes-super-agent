"""Tool planner — scores the catalog against a job and returns a ToolPlan.

The plan is what the agent surfaces to the user before acting:
  Tier 1 → 1-line banner
  Tier 2 → 4-line plan card + 3s grace + /cancel listener
  Tier 3 → hard stop; explicit YES required

This module stays pure: no I/O, no LLM calls. The catalog is loaded once at
plan time. The model recommendation comes from model_planner; this module
just calls it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_os.orchestrator import catalog as catalog_mod
from agent_os.orchestrator import tier_classifier
from agent_os.orchestrator.adapters.job_router import Job, route


@dataclass
class Alternative:
    name: str
    score: int
    reason: str


@dataclass
class ToolPlan:
    task_summary: str
    primary_tool: str
    primary_reason: str
    alternatives: list[Alternative] = field(default_factory=list)
    tier: int = 2
    tier_reason: str = ""
    estimated_cost_usd: float = 0.0
    estimated_seconds: int = 0
    risk_class: str = "low"
    grace_seconds: int = 0
    requires_explicit_confirm: bool = False
    model_recommendation: str | None = None
    model_reason: str = ""
    bundle_used: str = "primary_hermes"
    blocked_reason: str | None = None  # set when identity ceiling refuses tier
    signals: list[str] = field(default_factory=list)
    # True when this job will provision long-running infrastructure (a new
    # VPS or Railway service). Surfaced in plan_card so users see "permanent"
    # vs "ephemeral" before approving. Set from intent_classifier tags.
    permanent_resource: bool = False
    permanent_resource_kind: str = ""  # "vps" | "railway-service" | ""


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------

# Base score from the deterministic tag router (job_router.route).
# When the router's runtime matches a catalog entry, that tool gets +50.
ROUTER_MATCH_SCORE = 50

# Score boost for a tag appearing in the tool's category or description.
TAG_HIT_SCORE = 10

# Penalty for higher-tier tools when the task is cheap/idempotent.
TIER_PENALTY = {1: 0, 2: -2, 3: -8}


def _score_tool(
    tool_name: str,
    tool_data: dict[str, Any],
    job: Job,
    router_pick: str | None,
) -> tuple[int, str]:
    """Return (score, reason) for a single tool against a job."""
    score = 0
    reasons: list[str] = []

    if router_pick and tool_data.get("runtime") == router_pick:
        score += ROUTER_MATCH_SCORE
        reasons.append(f"router→{router_pick}")
    if router_pick and tool_name == router_pick:
        score += ROUTER_MATCH_SCORE
        if "router→" not in (reasons[0] if reasons else ""):
            reasons.append(f"router→{router_pick}")

    description = (tool_data.get("description") or "").lower()
    category = (tool_data.get("category") or "").lower()
    prompt_lower = job.prompt.lower()
    tags_lower = {t.lower() for t in job.tags}

    for tag in tags_lower:
        if not tag:
            continue
        if tag in description or tag in category:
            score += TAG_HIT_SCORE
            reasons.append(f"tag:{tag}")
    # Light prompt-keyword bonus — keep heuristic until embeddings land.
    for keyword in (
        "deck", "slides", "research", "investor",  # → openswarm
        "scrape", "browser", "form",               # → browser_use
        "shell", "grind", "files",                 # → openclaw
        "code", "test", "refactor",                # → claude_subagents/codex
        "voice", "audio", "realtime",              # → livekit
        "search", "find", "articles",              # → exa
    ):
        if keyword in prompt_lower and keyword in description:
            score += TAG_HIT_SCORE // 2
            reasons.append(f"kw:{keyword}")
            break

    score += TIER_PENALTY.get(int(tool_data.get("tier") or 2), 0)
    return score, ", ".join(dict.fromkeys(reasons)) or "default"


def _filter_by_bundle(
    tools: dict[str, dict[str, Any]],
    bundle: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return only the tools the identity bundle is allowed to use."""
    allowed = bundle.get("tools_allowed") or []
    denied = set(bundle.get("tools_denied") or [])
    if not allowed:
        return {n: t for n, t in tools.items() if n not in denied}
    return {n: t for n, t in tools.items() if n in allowed and n not in denied}


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def plan(
    job: Job,
    *,
    identity: str = "primary_hermes",
    catalog: dict[str, Any] | None = None,
) -> ToolPlan:
    """Score the catalog against `job` filtered by `identity`. Return a ToolPlan."""
    catalog = catalog if catalog is not None else catalog_mod.build_catalog()
    tools_all = catalog.get("tools", {})
    identities = catalog_mod.load_identities()
    bundle_data = identities.get(identity, {})

    # Primary Hermes has implicit access to everything (no tools_allowed in YAML).
    if identity == "primary_hermes":
        tools = tools_all
        ceiling: int | None = None
    else:
        tools = _filter_by_bundle(tools_all, bundle_data) or tools_all
        ceiling = bundle_data.get("default_tier_ceiling")

    router_pick = route(job)

    scored: list[tuple[int, str, str]] = []  # (score, name, reason)
    for name, data in tools.items():
        s, r = _score_tool(name, data, job, router_pick)
        scored.append((s, name, r))
    scored.sort(key=lambda x: -x[0])

    # If even the top scorer was 0 or negative, fall back to hermes_self.
    if not scored or scored[0][0] <= 0:
        primary_name = "hermes_self"
        primary_reason = "fallback: no strong match"
        rest = [s for s in scored if s[1] != primary_name][:2]
    else:
        primary_name = scored[0][1]
        primary_reason = scored[0][2]
        rest = [s for s in scored if s[1] != primary_name][:2]

    primary_data = tools.get(primary_name) or tools_all.get(primary_name) or {}
    alts = [Alternative(name=n, score=s, reason=r) for s, n, r in rest if s > 0]

    # Cost / time estimate from the tool's cost class.
    est_cost = _estimate_cost(primary_data.get("cost_class"))
    est_secs = _estimate_seconds(primary_data.get("cost_class"), primary_data.get("tier"))

    decision = tier_classifier.classify(
        job, cost_usd=est_cost, estimated_minutes=est_secs / 60.0
    )

    blocked = None
    if ceiling is not None and decision.tier > int(ceiling):
        blocked = (
            f"identity {identity!r} has default_tier_ceiling={ceiling}; "
            f"this task is tier {decision.tier}. Requires primary_hermes approval."
        )

    grace = {1: 0, 2: 3, 3: 0}[decision.tier]
    confirm = decision.tier == 3

    # Model recommendation — late import to avoid hard dep before F.3 ships.
    try:
        from agent_os.orchestrator import model_planner

        model_id, model_reason = model_planner.pick_model(
            task_class=primary_data.get("category", "default"),
            preferred=primary_data.get("preferred_models") or [],
        )
    except Exception:  # noqa: BLE001
        model_id, model_reason = None, "model_planner not yet available"

    # Permanent-infra detection. Same source of truth as tier_3_tags above
    # (intent_classifier emits these tags on natural-language spawn requests),
    # surfaced separately so the plan card can show an explicit "this will
    # provision a new VPS / Railway service" warning.
    from agent_os.orchestrator import intent_classifier
    is_permanent = intent_classifier.is_permanent_resource(job.tags)
    permanent_kind = ""
    lower_tags = {t.lower() for t in job.tags}
    if lower_tags & {"spawn-superagent", "vps-spawn", "spawn-vps"}:
        permanent_kind = "vps"
    elif lower_tags & {"build-specialist", "archon", "hire", "hire-agent",
                       "permanent-agent"}:
        permanent_kind = "railway-service"

    return ToolPlan(
        task_summary=_summarize(job.prompt),
        primary_tool=primary_name,
        primary_reason=primary_reason,
        alternatives=alts,
        tier=decision.tier,
        tier_reason=decision.reason,
        estimated_cost_usd=est_cost,
        estimated_seconds=est_secs,
        risk_class=primary_data.get("risk_class") or "low",
        grace_seconds=grace,
        requires_explicit_confirm=confirm,
        model_recommendation=model_id,
        model_reason=model_reason,
        bundle_used=identity,
        blocked_reason=blocked,
        signals=decision.signals,
        permanent_resource=is_permanent,
        permanent_resource_kind=permanent_kind,
    )


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

_COST_TABLE = {"low": 0.05, "medium": 0.40, "high": 2.50}
_SEC_TABLE = {"low": 30, "medium": 600, "high": 1800}


def _estimate_cost(cost_class: str | None) -> float:
    return _COST_TABLE.get((cost_class or "low").lower(), _COST_TABLE["low"])


def _estimate_seconds(cost_class: str | None, tier: int | None) -> int:
    base = _SEC_TABLE.get((cost_class or "low").lower(), _SEC_TABLE["low"])
    if tier == 3:
        return max(base, 3600)
    return base


def _summarize(prompt: str, max_chars: int = 80) -> str:
    snippet = " ".join(prompt.strip().split())
    if len(snippet) <= max_chars:
        return snippet
    return snippet[: max_chars - 1].rstrip() + "…"
