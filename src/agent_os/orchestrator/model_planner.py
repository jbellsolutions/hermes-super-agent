"""Model planner — picks a model based on the task class.

Rules from ``docs/routing-intelligence-contract.md`` plus the per-tool
``preferred_models`` lists in vault skills:

  - High-stakes (architecture / debug / security / auth / tests / deploy)
    → dual-frontier (draft model + review model).
  - Content / design / brand-voice → claude-opus-4.7.
  - Hard debug / security / auth → gpt-5.5.
  - Mechanical coding / data extraction → deepseek-v4-pro OR kimi-k2.
  - Default → claude-sonnet-4.7.

The planner is rule-based + deterministic; no LLM call here. Plan card
emission decides whether to actually invoke both halves of a dual-frontier
recommendation or just surface them.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _config_path() -> Path:
    return Path(__file__).with_name("config") / "models.yaml"


def load(path: Path | None = None) -> dict[str, Any]:
    p = path or _config_path()
    if not p.exists():
        return {"models": {}, "default_model": "claude-sonnet-4.7"}
    return yaml.safe_load(p.read_text()) or {}


def list_models(config: dict[str, Any] | None = None) -> dict[str, Any]:
    return (config or load()).get("models", {})


def pick_model(
    *,
    task_class: str,
    preferred: list[str] | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (model_id, reason).

    Order of precedence:
      1. The first item in ``preferred`` whose model exists in the registry
         AND that lists ``task_class`` in its ``task_classes`` (strong match).
      2. The first item in ``preferred`` that exists at all (preferred wins
         even without explicit task_class match).
      3. Any model whose ``task_classes`` contains the task class.
      4. ``default_model`` from config.
    """
    cfg = config or load()
    models = cfg.get("models", {})
    default = cfg.get("default_model", "claude-sonnet-4.7")
    preferred = preferred or []

    # 1. Preferred + strong task match
    for name in preferred:
        m = models.get(name)
        if m and task_class in (m.get("task_classes") or []):
            return name, f"preferred + matches task class {task_class!r}"

    # 2. Preferred (any registered)
    for name in preferred:
        if name in models:
            return name, "from tool's preferred_models"

    # 3. Any model with task class
    for name, m in models.items():
        if task_class in (m.get("task_classes") or []):
            return name, f"matches task class {task_class!r}"

    # 4. Default
    return default, "default — no task-class match"


def pick_dual_frontier(
    *,
    task_class: str,
    config: dict[str, Any] | None = None,
) -> tuple[str, str, str] | None:
    """Return (draft_model, review_model, reason) when the task class warrants it.

    Returns None if the task class is not in ``dual_frontier_task_classes``.
    """
    cfg = config or load()
    if task_class not in (cfg.get("dual_frontier_task_classes") or []):
        return None
    pairs = cfg.get("dual_frontier_pairs") or []
    if not pairs:
        return None
    draft, review = pairs[0]
    return draft, review, f"dual-frontier review for {task_class!r}"


def cost_estimate_usd(model_id: str, *, in_tokens: int, out_tokens: int,
                      config: dict[str, Any] | None = None) -> float:
    """Rough USD estimate from per-Mtok pricing."""
    cfg = config or load()
    m = cfg.get("models", {}).get(model_id)
    if not m:
        return 0.0
    return (
        (in_tokens / 1_000_000) * float(m.get("cost_per_mtok_in", 0))
        + (out_tokens / 1_000_000) * float(m.get("cost_per_mtok_out", 0))
    )
