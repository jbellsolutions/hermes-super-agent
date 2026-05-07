"""Unit tests for the model planner.

Covers the precedence order in pick_model(), dual-frontier emission, and
cost estimation arithmetic.
"""
from __future__ import annotations

import pytest

from agent_os.orchestrator import model_planner


@pytest.fixture(scope="module")
def cfg() -> dict:
    return model_planner.load()


# --------------------------------------------------------------------------
# load()
# --------------------------------------------------------------------------

def test_load_returns_models_dict(cfg):
    assert "models" in cfg
    assert "default_model" in cfg
    # All seven registered models present.
    assert len(cfg["models"]) == 8


def test_default_model_is_sonnet(cfg):
    assert cfg["default_model"] == "claude-sonnet-4.7"


# --------------------------------------------------------------------------
# pick_model precedence
# --------------------------------------------------------------------------

def test_preferred_with_task_match_wins(cfg):
    model_id, reason = model_planner.pick_model(
        task_class="architecture",
        preferred=["claude-opus-4.7", "gpt-5.5"],
        config=cfg,
    )
    assert model_id == "claude-opus-4.7"
    assert "preferred" in reason
    assert "architecture" in reason


def test_preferred_without_task_match_fallback(cfg):
    """Preferred model exists but doesn't list the task class — still picked."""
    model_id, reason = model_planner.pick_model(
        task_class="totally_unknown_class",
        preferred=["kimi-k2"],
        config=cfg,
    )
    assert model_id == "kimi-k2"
    assert "preferred_models" in reason


def test_task_class_match_when_no_preferred(cfg):
    model_id, _ = model_planner.pick_model(
        task_class="security", preferred=[], config=cfg,
    )
    assert model_id == "gpt-5.5"  # gpt-5.5 lists "security"


def test_default_when_nothing_matches(cfg):
    model_id, reason = model_planner.pick_model(
        task_class="zzz_nonexistent_class",
        preferred=["zzz_nonexistent_model"],
        config=cfg,
    )
    assert model_id == "claude-sonnet-4.7"
    assert "default" in reason


def test_unknown_preferred_skipped_then_task_class(cfg):
    model_id, _ = model_planner.pick_model(
        task_class="multimodal",
        preferred=["zzz_nonexistent_model"],
        config=cfg,
    )
    assert model_id == "gemini-2.5-pro"


# --------------------------------------------------------------------------
# dual-frontier
# --------------------------------------------------------------------------

@pytest.mark.parametrize("task_class", [
    "architecture", "debugging", "security", "authentication",
    "deployment", "high_risk_coding",
])
def test_dual_frontier_emitted_for_high_stakes(cfg, task_class):
    result = model_planner.pick_dual_frontier(task_class=task_class, config=cfg)
    assert result is not None
    draft, review, reason = result
    assert {draft, review} == {"claude-opus-4.7", "gpt-5.5"}
    assert task_class in reason


def test_dual_frontier_not_emitted_for_default(cfg):
    assert model_planner.pick_dual_frontier(
        task_class="content", config=cfg,
    ) is None


def test_dual_frontier_returns_none_for_unknown(cfg):
    assert model_planner.pick_dual_frontier(
        task_class="not_a_real_class", config=cfg,
    ) is None


# --------------------------------------------------------------------------
# cost_estimate_usd
# --------------------------------------------------------------------------

def test_cost_estimate_kimi_k2(cfg):
    # 1M in @ $0.15 + 1M out @ $2.50 = $2.65
    cost = model_planner.cost_estimate_usd(
        "kimi-k2", in_tokens=1_000_000, out_tokens=1_000_000, config=cfg,
    )
    assert cost == pytest.approx(2.65, abs=0.01)


def test_cost_estimate_opus(cfg):
    # 100k in @ $15 + 100k out @ $75 = $1.50 + $7.50 = $9.00
    cost = model_planner.cost_estimate_usd(
        "claude-opus-4.7", in_tokens=100_000, out_tokens=100_000, config=cfg,
    )
    assert cost == pytest.approx(9.00, abs=0.01)


def test_cost_estimate_unknown_model_is_zero(cfg):
    cost = model_planner.cost_estimate_usd(
        "made-up-model", in_tokens=1_000_000, out_tokens=1_000_000, config=cfg,
    )
    assert cost == 0.0


# --------------------------------------------------------------------------
# DeepSeek v4 Pro guard (user-corrected)
# --------------------------------------------------------------------------

def test_deepseek_is_v4_pro_not_v3(cfg):
    assert "deepseek-v4-pro" in cfg["models"]
    assert "deepseek-v3" not in cfg["models"]
    deepseek = cfg["models"]["deepseek-v4-pro"]
    assert "v4 Pro" in (deepseek.get("notes") or "")


def test_mechanical_coding_can_pick_deepseek(cfg):
    """Either DeepSeek or Kimi should win for mechanical_coding (both list it)."""
    model_id, _ = model_planner.pick_model(
        task_class="mechanical_coding", preferred=[], config=cfg,
    )
    assert model_id in ("deepseek-v4-pro", "kimi-k2")


# --------------------------------------------------------------------------
# list_models
# --------------------------------------------------------------------------

def test_list_models_returns_dict(cfg):
    models = model_planner.list_models(cfg)
    assert isinstance(models, dict)
    assert len(models) == 8
