"""Unit tests for the tool catalog generator.

The catalog merges per-tool SKILL.md frontmatter + runtime manifests +
identity packs + model registry into a single dict and writes
``vault/graph/tool-catalog.yaml`` plus the cheatsheet.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from agent_os.orchestrator import catalog


def test_load_skills_finds_all_15_tools():
    skills = catalog.load_skills()
    # Phase F ships 15 tools — guard against accidental deletion.
    assert len(skills) >= 15
    # Spot-check the headline ones.
    for name in ("openswarm", "openclaw", "hermes_self", "browser_use",
                 "computer_use", "exa", "terminal", "composio"):
        assert name in skills, f"missing skill: {name}"


def test_skill_frontmatter_has_required_fields():
    skills = catalog.load_skills()
    for name, skill in skills.items():
        assert skill.get("description"), f"{name} missing description"
        assert skill.get("tier") in (1, 2, 3), f"{name} bad tier: {skill.get('tier')}"
        assert skill.get("cost_class") in ("low", "medium", "high"), name
        assert skill.get("risk_class") in ("low", "medium", "high"), name


def test_load_models_returns_seven():
    models = catalog.load_models()
    assert len(models) == 7
    # Each must register pricing — guard against accidental schema regression.
    for name, m in models.items():
        assert "cost_per_mtok_in" in m, name
        assert "cost_per_mtok_out" in m, name
        assert "task_classes" in m, name


def test_load_models_includes_deepseek_v4_pro():
    """User explicitly corrected v3 → v4 pro; guard the registry."""
    models = catalog.load_models()
    assert "deepseek-v4-pro" in models
    assert "deepseek-v3" not in models


def test_load_models_includes_kimi_and_gemini():
    models = catalog.load_models()
    assert "kimi-k2" in models
    assert "gemini-2.5-pro" in models


def test_load_identities_includes_coo_with_ceiling():
    identities = catalog.load_identities()
    assert "coo" in identities
    coo = identities["coo"]
    assert coo.get("default_tier_ceiling") == 2
    assert "tools_allowed" in coo
    assert "tools_denied" in coo


def test_build_catalog_shape():
    cat = catalog.build_catalog()
    assert "generated_at" in cat
    assert "tools" in cat
    assert "bundles" in cat
    assert "models" in cat
    assert len(cat["tools"]) >= 15
    assert len(cat["models"]) == 7


def test_build_catalog_assigns_bundles_to_tools():
    cat = catalog.build_catalog()
    # primary_hermes inherits everything (no tools_allowed in its YAML).
    if "primary_hermes" in cat["bundles"]:
        # All tools should have it in available_to_bundles.
        for tool_name, tool_data in cat["tools"].items():
            assert "primary_hermes" in tool_data["available_to_bundles"], tool_name


def test_coo_bundle_excludes_terminal():
    cat = catalog.build_catalog()
    coo_tools = cat["bundles"].get("coo", [])
    assert "terminal" not in coo_tools, "COO must not have terminal access"
    assert "claude_managed" not in coo_tools
    assert "e2b" not in coo_tools


def test_coo_bundle_includes_openswarm():
    cat = catalog.build_catalog()
    coo_tools = cat["bundles"].get("coo", [])
    assert "openswarm" in coo_tools


def test_extract_alternatives_parses_section():
    body = """
## When to use
- Quick demo

## Alternatives (ordered by closeness)
1. **hermes_self** — for simpler asks
2. **openclaw** — when grind dominates
3. **claude_managed** — for very long jobs

## Cost & latency
- Typical
"""
    alts = catalog._extract_alternatives(body)
    assert alts == ["hermes_self", "openclaw", "claude_managed"]


def test_extract_alternatives_empty_when_section_missing():
    assert catalog._extract_alternatives("## Random\n- nothing here") == []


def test_render_cheatsheet_includes_all_tools():
    cat = catalog.build_catalog()
    text = catalog.render_cheatsheet(cat)
    for name in cat["tools"]:
        assert f"`{name}`" in text, f"cheatsheet missing {name}"
    # markdown table header
    assert "| Tool | Tier | Category |" in text


def test_write_catalog_round_trips(tmp_path: Path):
    cat = catalog.build_catalog()
    out = catalog.write_catalog(cat, out_path=tmp_path / "tool-catalog.yaml")
    assert out.exists()
    parsed = yaml.safe_load(out.read_text())
    assert parsed["tools"].keys() == cat["tools"].keys()
    assert len(parsed["models"]) == len(cat["models"])


def test_show_tool_known(tmp_path):
    text = catalog.show_tool("openswarm")
    assert "openswarm" in text.lower()
    # frontmatter delimiters present
    assert text.lstrip().startswith("---")


def test_show_tool_unknown_lists_known():
    text = catalog.show_tool("definitely_not_a_real_tool_xyz")
    assert "Tool not found" in text
    assert "openswarm" in text  # known list rendered
