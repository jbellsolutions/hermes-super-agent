"""Intent classifier — turn natural-language prompts into routing tags.

Used by channel adapters (Telegram, Slack, web) to enrich a Job's tag set
*before* the planner runs. The point is to make the difference between
the three execution lanes explicit and gated:

  Lane A — Ephemeral sub-agent (default, ~90% of jobs)
    "research these 3 startups" / "summarize the news" / "draft an email"
    → no tag added, planner falls through to hermes_self, runs in-process,
      no new infra, no recurring cost.

  Lane B — Outsourced fan-out via the existing Coordinator service (~8%)
    "do this 100 ways in parallel" / "fan out this research" /
    "run a swarm on these 50 leads"
    → 'fan-out' tag, routes to the deployed Coordinator (one Railway
      service that already exists), no NEW infra spun up.

  Lane C — Permanent superagent / specialist (~2%, never auto-fires)
    "spin up a cold email superagent" / "hire a LinkedIn specialist" /
    "build me a permanent SDR agent"
    → 'spawn-superagent' or 'build-specialist' tag, planner forces
      Tier 3 hard stop. User MUST reply YES. Provisions new VPS
      (DigitalOcean) or new Railway service.

This module is pure: no I/O, no LLM call. The classifier is a regex
pass with a small phrase dictionary so behavior is deterministic and
testable. If we ever need fuzzier intent matching, add a single
LLM-backed fallback path — but never bypass the Tier 3 gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Permanence cues — these phrases mean "stand up a long-running agent"
# (a new VPS / Railway service). Tier 3, requires YES.
# --------------------------------------------------------------------------

# Permanence verbs paired with a noun that implies long-running infra.
# Use `[\w\s\-]*?` (lazy, allows multi-word qualifiers like "cold email")
# so prompts like "spin up a cold email superagent" still match.
_SPAWN_VPS_PHRASES = [
    r"\bspin\s+up\s+([\w\s\-]*?)?(superagent|super\s*agent)\b",
    r"\bspawn\s+([\w\s\-]*?)?(superagent|super\s*agent|vps|droplet)\b",
    r"\bhire\s+([\w\s\-]*?)?(agent|superagent|specialist|operator)\b",
    r"\b(create|build|deploy|stand\s+up)\s+([\w\s\-]*?)?permanent\s+([\w\s\-]*?)?(agent|superagent|specialist|hermes)\b",
    r"\b(provision|spin\s+up|deploy)\s+([\w\s\-]*?)?(vps|droplet)\b",
    r"\bnew\s+(superagent|super\s*agent)\b",
    r"\bdedicated\s+(agent|superagent|hermes)\b",
]

_BUILD_SPECIALIST_PHRASES = [
    r"\bbuild\s+(me\s+)?(a|an)\s+[\w\s\-]*?(specialist|agent|operator)\s+(that|to|who)\b",
    r"\bcreate\s+(me\s+)?(a|an)\s+[\w\s\-]*?(specialist|agent|operator)\s+(that|to|who)\b",
    r"\bgenerate\s+(me\s+)?(a|an)\s+[\w\s\-]*?(specialist|agent)\b",
    r"\bdesign\s+(me\s+)?(a|an)\s+(new\s+)?[\w\s\-]*?(specialist|agent)\b",
]

# --------------------------------------------------------------------------
# Fan-out cues — outsourced parallel work via the existing Coordinator.
# No NEW infra; just heavier use of the Railway service that's already up.
# --------------------------------------------------------------------------

_FANOUT_PHRASES = [
    r"\bfan(\s|-)?out\b",
    r"\b\d+\s*(ways|variants|sub\s*agents|sub-agents|sub_agents|copies)\b",
    r"\bin\s+parallel\b",
    r"\bparallel\s+sub\s*agents\b",
    r"\bswarm\s+(on|over|across)\b",
    r"\bcoordinator\b",
    r"\b(run|do)\s+this\s+\d+\s+(ways|times)\b",
]

# --------------------------------------------------------------------------
# Outbound channel cues — phone / email. These already gate Tier 3 in
# tiers.yaml; we just ensure the routing tag is set so the COO Specialist
# runtime gets dispatched.
# --------------------------------------------------------------------------

_OUTBOUND_PHONE_PHRASES = [
    r"\b(call|phone|dial|ring)\s+\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b",
    r"\b(make|place)\s+(a|an|the)?\s*(phone|outbound)\s+call\b",
    r"\boutbound\s+phone\b",
    r"\bcold\s+call\b",
]

_OUTBOUND_EMAIL_PHRASES = [
    r"\bcold\s+email\b",
    r"\bsend\s+(a|an|the)\s+cold\s+email\b",
    r"\boutbound\s+(?:email\s+)?campaign\b",
    r"\bemail\s+campaign\b",
]


@dataclass
class IntentResult:
    tags: set[str]
    matched_phrases: list[str]


def classify(prompt: str) -> IntentResult:
    """Return inferred tags for `prompt`. Empty set means 'no spawn intent —
    let the planner default to in-process hermes_self.'

    Matching is case-insensitive, regex-based, and order-independent.
    Multiple intents can co-occur (a fan-out request that also mentions
    cold email gets both `fan-out` and `outbound-email`).
    """
    text = (prompt or "").lower()
    if not text.strip():
        return IntentResult(tags=set(), matched_phrases=[])

    tags: set[str] = set()
    matched: list[str] = []

    for pat in _SPAWN_VPS_PHRASES:
        if re.search(pat, text):
            tags.add("spawn-superagent")
            matched.append(f"spawn-vps:{pat}")
            break

    for pat in _BUILD_SPECIALIST_PHRASES:
        if re.search(pat, text):
            tags.add("build-specialist")
            matched.append(f"build-specialist:{pat}")
            break

    for pat in _FANOUT_PHRASES:
        if re.search(pat, text):
            tags.add("fan-out")
            matched.append(f"fan-out:{pat}")
            break

    for pat in _OUTBOUND_PHONE_PHRASES:
        if re.search(pat, text):
            tags.add("outbound-phone")
            matched.append(f"outbound-phone:{pat}")
            break

    for pat in _OUTBOUND_EMAIL_PHRASES:
        if re.search(pat, text):
            tags.add("outbound-email")
            matched.append(f"outbound-email:{pat}")
            break

    return IntentResult(tags=tags, matched_phrases=matched)


def is_permanent_resource(tags: set[str]) -> bool:
    """True when the tags indicate a job that provisions long-running infra.

    The plan card uses this to print an explicit '⚠ permanent infrastructure'
    warning and an estimate of recurring cost. tier_classifier.yaml already
    forces these tags to Tier 3 — this helper just lets the UI explain why.
    """
    permanent = {
        "spawn-superagent", "vps-spawn", "spawn-vps",
        "build-specialist", "archon",
        "hire", "hire-agent", "permanent-agent",
    }
    return bool({t.lower() for t in tags} & permanent)
