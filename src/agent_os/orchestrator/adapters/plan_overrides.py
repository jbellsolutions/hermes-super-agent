"""Override surface — parses user commands that intercept a plan card.

Commands accepted (case-insensitive except YES):

  /cancel             abort the task
  /use <tool>         replace the primary tool; optionally add a model:
                      `/use openclaw kimi-k2`
  /why                emit the long-form explanation (handled in plan_card)
  /plan on            per-session: emit cards for ALL tiers including 1
  /plan off           per-session: only emit for tier >= 2
  /tier 1             force this task to tier 1 (refused for destructive ops)
  /tier 2             force this task to tier 2
  /tier 3             force this task to tier 3
  YES                 explicit confirmation for tier 3 (UPPERCASE required)

Output is a structured Override dataclass; the integration layer (Hermes
turn handler / channel adapter) decides how to apply it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

OverrideKind = Literal[
    "cancel", "use", "why", "plan_on", "plan_off",
    "tier", "confirm", "identity", "unknown",
]


@dataclass
class Override:
    kind: OverrideKind
    raw: str
    tool: str | None = None
    model: str | None = None
    tier: int | None = None
    identity: str | None = None
    error: str | None = None


_USE_RE = re.compile(r"^/use\s+([A-Za-z0-9_]+)(?:\s+([A-Za-z0-9_.-]+))?\s*$")
_TIER_RE = re.compile(r"^/tier\s+([123])\s*$")
_IDENTITY_RE = re.compile(r"^/identity(?:\s+([A-Za-z0-9_]+))?\s*$")


def parse(text: str) -> Override | None:
    """Return an Override if the text matches a known command, else None.

    None means "this isn't a command" — the caller should treat the message
    as ordinary chat input.
    """
    if text is None:
        return None
    raw = text.strip()
    if not raw:
        return None

    # YES is case-sensitive (uppercase only) so it can't be triggered by lowercase
    # 'yes' in conversational replies.
    if raw == "YES":
        return Override(kind="confirm", raw=raw)

    # Other commands are case-insensitive on the leading slash word.
    lower = raw.lower()

    if lower == "/cancel":
        return Override(kind="cancel", raw=raw)
    if lower == "/why":
        return Override(kind="why", raw=raw)
    if lower in ("/plan on", "/plan_on"):
        return Override(kind="plan_on", raw=raw)
    if lower in ("/plan off", "/plan_off"):
        return Override(kind="plan_off", raw=raw)

    if lower.startswith("/use"):
        m = _USE_RE.match(lower)
        if not m:
            return Override(
                kind="unknown",
                raw=raw,
                error="usage: /use <tool> [<model>]",
            )
        return Override(kind="use", raw=raw, tool=m.group(1), model=m.group(2))

    if lower.startswith("/tier"):
        m = _TIER_RE.match(lower)
        if not m:
            return Override(
                kind="unknown",
                raw=raw,
                error="usage: /tier <1|2|3>",
            )
        return Override(kind="tier", raw=raw, tier=int(m.group(1)))

    if lower.startswith("/identity"):
        m = _IDENTITY_RE.match(lower)
        if not m:
            return Override(
                kind="unknown",
                raw=raw,
                error="usage: /identity <name>  (e.g. /identity coo)",
            )
        return Override(kind="identity", raw=raw, identity=m.group(1))

    if raw.startswith("/"):
        return Override(
            kind="unknown",
            raw=raw,
            error=f"unknown command: {raw.split()[0]}",
        )
    return None


def is_command(text: str | None) -> bool:
    """True iff `parse(text)` would return a recognized override (not None)."""
    return parse(text or "") is not None
