"""Plan card emitter — renders a ToolPlan into one of three formats:

  Tier 1: 1-line banner
    ⚡ using `read_files` · sonnet-4.7

  Tier 2: 4-line plan card
    📋 Plan: research AI agent market → deck
    • Tools: openswarm/auto (slides+research+docs); alts: hermes_self
    • Model: claude-opus-4.7 (alt: gpt-5.5)
    • Tier 2 · ~$0.30 · ~12min · proceeding in 3s · /cancel /use /why

  Tier 3: hard stop
    🛑 Plan: deploy main to production
    • Tools: terminal, github
    • Model: gpt-5.5
    • Tier 3 · destructive · reply YES to proceed

Rendering targets:
  - markdown (default — works in CLI, Slack, Telegram, web chat)
  - json (for API consumers / dashboard / programmatic flows)

Plan blocking by identity ceiling produces a 4th format: the Tier 3 card
with a "blocked" suffix — caller decides whether to escalate or refuse.
"""
from __future__ import annotations

import json
from typing import Any

from agent_os.orchestrator.tool_planner import Alternative, ToolPlan

# --------------------------------------------------------------------------
# markdown
# --------------------------------------------------------------------------

def render_markdown(plan: ToolPlan) -> str:
    if plan.blocked_reason:
        return _render_blocked(plan)
    if plan.tier == 1:
        return _render_tier_1(plan)
    if plan.tier == 2:
        return _render_tier_2(plan)
    return _render_tier_3(plan)


def _render_tier_1(plan: ToolPlan) -> str:
    model = plan.model_recommendation or "default"
    return f"⚡ using `{plan.primary_tool}` · {model}"


def _render_tier_2(plan: ToolPlan) -> str:
    alts = _alts_summary(plan.alternatives, max_alts=2)
    model = plan.model_recommendation or "default"
    cost = f"~${plan.estimated_cost_usd:.2f}"
    minutes = max(1, round(plan.estimated_seconds / 60.0))
    lines = [
        f"📋 Plan: {plan.task_summary}",
        f"  • Tools: {plan.primary_tool} ({plan.primary_reason}); alts: {alts}",
        f"  • Model: {model}{' (' + plan.model_reason + ')' if plan.model_reason else ''}",
        f"  • Tier 2 · {cost} · ~{minutes}min · reply 'yes' to run · /cancel /use <tool> /why",
    ]
    return "\n".join(lines)


def _render_tier_3(plan: ToolPlan) -> str:
    alts = _alts_summary(plan.alternatives, max_alts=1)
    model = plan.model_recommendation or "default"
    cost = f"~${plan.estimated_cost_usd:.2f}"
    flavor = (
        "destructive" if plan.risk_class == "high"
        else "expensive" if plan.estimated_cost_usd > 1.0
        else "high-impact"
    )
    lines = [
        f"🛑 Plan: {plan.task_summary}",
        f"  • Tools: {plan.primary_tool} ({plan.primary_reason}); alts: {alts}",
        f"  • Model: {model}",
        f"  • Tier 3 · {flavor} · {cost} · reply YES to proceed (/cancel /use <tool> /why)",
    ]
    return "\n".join(lines)


def _render_blocked(plan: ToolPlan) -> str:
    return (
        f"🚫 Blocked: {plan.task_summary}\n"
        f"  • Tools requested: {plan.primary_tool} (tier {plan.tier})\n"
        f"  • {plan.blocked_reason}"
    )


def _alts_summary(alts: list[Alternative], max_alts: int = 2) -> str:
    if not alts:
        return "—"
    return ", ".join(a.name for a in alts[:max_alts])


# --------------------------------------------------------------------------
# json
# --------------------------------------------------------------------------

def render_json(plan: ToolPlan) -> str:
    return json.dumps(_to_dict(plan), indent=2)


def _to_dict(plan: ToolPlan) -> dict[str, Any]:
    return {
        "task_summary": plan.task_summary,
        "primary_tool": plan.primary_tool,
        "primary_reason": plan.primary_reason,
        "alternatives": [
            {"name": a.name, "score": a.score, "reason": a.reason}
            for a in plan.alternatives
        ],
        "tier": plan.tier,
        "tier_reason": plan.tier_reason,
        "estimated_cost_usd": plan.estimated_cost_usd,
        "estimated_seconds": plan.estimated_seconds,
        "risk_class": plan.risk_class,
        "grace_seconds": plan.grace_seconds,
        "requires_explicit_confirm": plan.requires_explicit_confirm,
        "model_recommendation": plan.model_recommendation,
        "model_reason": plan.model_reason,
        "bundle_used": plan.bundle_used,
        "blocked_reason": plan.blocked_reason,
        "signals": plan.signals,
    }


# --------------------------------------------------------------------------
# /why explanation (longer; called by override surface)
# --------------------------------------------------------------------------

def render_why(plan: ToolPlan) -> str:
    """5-line explanation of how the plan was chosen. Used by the /why command."""
    lines = [
        f"📌 Why this plan for: {plan.task_summary}",
        f"  • Picked: {plan.primary_tool} — {plan.primary_reason}",
        f"  • Tier: {plan.tier} ({plan.tier_reason})",
    ]
    if plan.alternatives:
        scored = ", ".join(
            f"{a.name}({a.score})" for a in plan.alternatives[:3]
        )
        lines.append(f"  • Other candidates: {scored}")
    if plan.model_recommendation:
        lines.append(f"  • Model: {plan.model_recommendation} — {plan.model_reason}")
    if plan.signals:
        lines.append(f"  • Signals: {', '.join(plan.signals[:5])}")
    return "\n".join(lines)


def render(plan: ToolPlan, channel: str = "markdown") -> str:
    """Channel-aware dispatch. Defaults to markdown."""
    channel = (channel or "markdown").lower()
    if channel == "json":
        return render_json(plan)
    if channel == "why":
        return render_why(plan)
    return render_markdown(plan)
