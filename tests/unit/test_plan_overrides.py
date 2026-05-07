"""Unit tests for the override surface.

Parses commands like /cancel /use /why /plan on|off /tier N YES.
"""
from __future__ import annotations

import pytest

from agent_os.orchestrator.adapters import plan_overrides as ov

# --------------------------------------------------------------------------
# basic parsing — recognized commands
# --------------------------------------------------------------------------

def test_cancel():
    o = ov.parse("/cancel")
    assert o is not None
    assert o.kind == "cancel"
    assert o.error is None


def test_cancel_case_insensitive():
    assert ov.parse("/CANCEL").kind == "cancel"
    assert ov.parse("/Cancel").kind == "cancel"


def test_why():
    assert ov.parse("/why").kind == "why"


def test_plan_on():
    assert ov.parse("/plan on").kind == "plan_on"
    assert ov.parse("/plan_on").kind == "plan_on"


def test_plan_off():
    assert ov.parse("/plan off").kind == "plan_off"
    assert ov.parse("/plan_off").kind == "plan_off"


# --------------------------------------------------------------------------
# /use parsing
# --------------------------------------------------------------------------

def test_use_tool_only():
    o = ov.parse("/use openclaw")
    assert o.kind == "use"
    assert o.tool == "openclaw"
    assert o.model is None


def test_use_tool_and_model():
    o = ov.parse("/use openclaw kimi-k2")
    assert o.kind == "use"
    assert o.tool == "openclaw"
    assert o.model == "kimi-k2"


def test_use_invalid_returns_unknown_with_usage():
    o = ov.parse("/use")
    assert o.kind == "unknown"
    assert "usage" in o.error.lower()


def test_use_with_special_chars_rejected():
    o = ov.parse("/use ./../etc")
    assert o.kind == "unknown"


# --------------------------------------------------------------------------
# /tier parsing
# --------------------------------------------------------------------------

@pytest.mark.parametrize("level", [1, 2, 3])
def test_tier_valid(level):
    o = ov.parse(f"/tier {level}")
    assert o.kind == "tier"
    assert o.tier == level


def test_tier_invalid_level():
    o = ov.parse("/tier 4")
    assert o.kind == "unknown"
    assert "usage" in o.error.lower()


def test_tier_no_arg():
    o = ov.parse("/tier")
    assert o.kind == "unknown"


# --------------------------------------------------------------------------
# YES — case-sensitive uppercase only
# --------------------------------------------------------------------------

def test_yes_uppercase_confirms():
    o = ov.parse("YES")
    assert o is not None
    assert o.kind == "confirm"


def test_lowercase_yes_is_not_a_command():
    """Don't auto-confirm tier 3 from a casual 'yes' reply."""
    assert ov.parse("yes") is None
    assert ov.parse("Yes") is None


def test_yes_with_extra_text_is_not_command():
    assert ov.parse("YES please") is None


# --------------------------------------------------------------------------
# unknown / non-commands
# --------------------------------------------------------------------------

def test_unknown_slash_returns_unknown():
    o = ov.parse("/totally-not-a-command")
    assert o is not None
    assert o.kind == "unknown"
    assert "unknown command" in o.error


def test_plain_text_returns_none():
    assert ov.parse("just chatting") is None


def test_empty_returns_none():
    assert ov.parse("") is None
    assert ov.parse("   ") is None
    assert ov.parse(None) is None


# --------------------------------------------------------------------------
# is_command convenience
# --------------------------------------------------------------------------

def test_is_command_true_for_known():
    assert ov.is_command("/cancel") is True
    assert ov.is_command("YES") is True
    assert ov.is_command("/use openclaw") is True


def test_is_command_true_for_unknown_slash():
    """An unknown /xxx is still a command (parsed as kind=unknown)."""
    assert ov.is_command("/notreal") is True


def test_is_command_false_for_chat():
    assert ov.is_command("hello there") is False
    assert ov.is_command(None) is False
    assert ov.is_command("") is False


# --------------------------------------------------------------------------
# whitespace tolerance
# --------------------------------------------------------------------------

def test_leading_trailing_whitespace_ok():
    assert ov.parse("  /cancel  ").kind == "cancel"
    assert ov.parse("\t/why\n").kind == "why"
