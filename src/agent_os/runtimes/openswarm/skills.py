"""Render and write per-swarm routing skills into vault/skills/active/.

Each registered swarm gets a SKILL.md whose `description:` field is what
Hermes' router scores against. Builder (Phase B) calls render_for() after a
successful build; Phase A bootstraps the default swarm via render_default().
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()
ACTIVE_DIR = VAULT_ROOT / "skills" / "active"
TEMPLATE_PATH = Path(__file__).with_name("skill_template.md")

DEFAULT_DESCRIPTION = (
    "Use when the user asks for multi-deliverable production (slide decks, "
    "investor pitches, research reports, executive summaries with charts, "
    "blog posts with images, etc.). Routes to the default OpenSwarm fleet "
    "member which orchestrates research → analysis → slides → docs."
)
DEFAULT_BUSINESS_PURPOSE = (
    "Default OpenSwarm: general multi-agent deliverable production "
    "(slides, research, decks, docs, charts, images, video)."
)
DEFAULT_OUTPUT_TYPES = "slide decks, research reports, executive summaries, charts, images"
DEFAULT_EXAMPLES = [
    "Create a complete investor pitch for {topic}.",
    "Research {market} and turn the findings into a 10-slide deck.",
    "Generate an executive summary plus charts for {dataset}.",
]


def _format_examples(examples: list[str]) -> str:
    return "\n".join(f"- {ex}" for ex in examples)


def render_for(
    name: str,
    *,
    description: str,
    business_purpose: str,
    output_types: str,
    examples: list[str],
    cost_budget_daily_usd: float,
    manifest_path: str | os.PathLike[str],
) -> Path:
    """Render and write vault/skills/active/<name>-swarm.md. Returns the path."""
    template = TEMPLATE_PATH.read_text()
    rendered = template.format(
        name=name,
        description=description,
        business_purpose=business_purpose,
        output_types=output_types,
        example_block=_format_examples(examples),
        cost_budget_daily_usd=cost_budget_daily_usd,
        manifest_path=str(manifest_path),
    )
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    out = ACTIVE_DIR / f"{name}-swarm.md"
    out.write_text(rendered)
    return out


def render_default(manifest_path: str | os.PathLike[str] = "vendor/openswarm") -> Path:
    return render_for(
        "default",
        description=DEFAULT_DESCRIPTION,
        business_purpose=DEFAULT_BUSINESS_PURPOSE,
        output_types=DEFAULT_OUTPUT_TYPES,
        examples=DEFAULT_EXAMPLES,
        cost_budget_daily_usd=10.0,
        manifest_path=manifest_path,
    )


def derive_description(business_purpose: str, examples: list[str]) -> str:
    """Build a router-friendly `description:` line from a build prompt.

    Hermes' router scores the SKILL.md description against the user's prompt,
    so this string carries most of the routing weight. We surface keywords
    explicitly via 'Use when the user asks about ...' phrasing.
    """
    snippet = business_purpose.strip().rstrip(".")
    base = f"Use when the user asks about {snippet}."
    if examples:
        first = examples[0].rstrip(".")
        base += f" Example: {first}."
    return base


def remove_for(name: str) -> bool:
    out = ACTIVE_DIR / f"{name}-swarm.md"
    if out.exists():
        out.unlink()
        return True
    return False


def render_from_registry_entry(name: str, entry: dict[str, Any]) -> Path:
    """Bootstrap a SKILL.md from a registry entry that may not carry full metadata.

    Used by Phase A's `provision_default` flow and as a recovery hook.
    """
    description = entry.get("description") or (
        DEFAULT_DESCRIPTION if name == "default" else
        f"Use when the user asks about {entry.get('business_purpose', name)}."
    )
    return render_for(
        name,
        description=description,
        business_purpose=entry.get("business_purpose", DEFAULT_BUSINESS_PURPOSE),
        output_types=entry.get("output_types", DEFAULT_OUTPUT_TYPES),
        examples=entry.get("examples", DEFAULT_EXAMPLES),
        cost_budget_daily_usd=float(entry.get("cost_budget_daily_usd", 10.0)),
        manifest_path=entry.get("manifest", "vendor/openswarm"),
    )
