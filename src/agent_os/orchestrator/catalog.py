"""Tool catalog generator — single source of truth that merges:

  - Per-tool SKILL.md frontmatter from ``vault/skills/active/tools/``
  - Per-runtime manifest.yaml from ``src/agent_os/runtimes/<name>/manifest.yaml``
  - Identity-pack tool bundles from ``src/agent_os/orchestrator/config/identities/``
  - Model registry from ``src/agent_os/orchestrator/config/models.yaml``

The output ``vault/graph/tool-catalog.yaml`` is read by the planner, the
``/explain`` skill, and the dashboard. Regenerate via ``agent-os catalog``.
"""
from __future__ import annotations

import datetime as dt
import os
import re
from pathlib import Path
from typing import Any

import yaml


def repo_root() -> Path:
    """Resolve the repo root from this file's location."""
    return Path(__file__).resolve().parents[3]


def vault_root() -> Path:
    return Path(os.environ.get("VAULT_ROOT", repo_root() / "vault")).resolve()


# --------------------------------------------------------------------------
# parsers
# --------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_skill(path: Path) -> dict[str, Any]:
    """Extract frontmatter + lead body from a SKILL.md file."""
    text = path.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {"name": path.stem, "skill_path": str(path), "_raw_only": True}
    fm = yaml.safe_load(match.group(1)) or {}
    body = text[match.end():]
    fm.setdefault("name", path.stem)
    fm["skill_path"] = str(path.relative_to(repo_root()))
    fm["body"] = body
    return fm


def load_skills(tools_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    tools_dir = tools_dir or (vault_root() / "skills" / "active" / "tools")
    if not tools_dir.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(tools_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        skill = parse_skill(path)
        out[skill["name"]] = skill
    return out


def load_runtime_manifests(runtimes_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    runtimes_dir = runtimes_dir or (repo_root() / "src" / "agent_os" / "runtimes")
    out: dict[str, dict[str, Any]] = {}
    if not runtimes_dir.exists():
        return out
    for child in sorted(runtimes_dir.iterdir()):
        manifest = child / "manifest.yaml"
        if not manifest.exists():
            continue
        try:
            data = yaml.safe_load(manifest.read_text()) or {}
        except yaml.YAMLError:
            continue
        data["manifest_path"] = str(manifest.relative_to(repo_root()))
        out[child.name] = data
    return out


def load_identities(identities_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    identities_dir = identities_dir or (
        repo_root() / "src" / "agent_os" / "orchestrator" / "config" / "identities"
    )
    out: dict[str, dict[str, Any]] = {}
    if not identities_dir.exists():
        return out
    for path in sorted(identities_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            continue
        data["identity_path"] = str(path.relative_to(repo_root()))
        out[path.stem] = data
    return out


def load_models(models_path: Path | None = None) -> dict[str, dict[str, Any]]:
    models_path = models_path or (
        repo_root() / "src" / "agent_os" / "orchestrator" / "config" / "models.yaml"
    )
    if not models_path.exists():
        return {}
    try:
        data = yaml.safe_load(models_path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    return data.get("models", {})


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build_catalog() -> dict[str, Any]:
    """Compose the merged catalog dict. Pure function — no I/O."""
    skills = load_skills()
    runtimes = load_runtime_manifests()
    identities = load_identities()
    models = load_models()

    tools: dict[str, dict[str, Any]] = {}
    for name, skill in skills.items():
        manifest = runtimes.get(skill.get("runtime", name)) or {}
        tools[name] = {
            "name": name,
            "runtime": skill.get("runtime", name),
            "tier": skill.get("tier"),
            "category": skill.get("category"),
            "cost_class": skill.get("cost_class"),
            "risk_class": skill.get("risk_class"),
            "preferred_models": skill.get("preferred_models", []),
            "mcp_or_native": skill.get("mcp_or_native"),
            "description": skill.get("description"),
            "skill_path": skill.get("skill_path"),
            "manifest_path": manifest.get("manifest_path"),
            "manifest_description": manifest.get("description"),
            "available_to_bundles": [],  # populated below
            "alternatives": _extract_alternatives(skill.get("body", "")),
        }

    # Reverse-index: which bundles include which tool?
    bundles: dict[str, list[str]] = {}
    for ident_name, ident_data in identities.items():
        allowed = ident_data.get("tools_allowed") or []
        denied = set(ident_data.get("tools_denied") or [])
        # If tools_allowed is empty, infer "all except denied" (legacy behavior).
        effective = (
            [t for t in tools if t not in denied]
            if not allowed
            else [t for t in allowed if t not in denied]
        )
        bundles[ident_name] = effective
        for tool_name in effective:
            if tool_name in tools:
                tools[tool_name]["available_to_bundles"].append(ident_name)

    return {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "tools": tools,
        "bundles": bundles,
        "models": models,
    }


_ALT_LIST_RE = re.compile(r"\*\*([A-Za-z0-9_]+)\*\*", re.MULTILINE)


def _extract_alternatives(body: str) -> list[str]:
    """Pull tool names from the '## Alternatives' section of a skill body."""
    if "## Alternatives" not in body:
        return []
    section = body.split("## Alternatives", 1)[1]
    section = section.split("\n## ", 1)[0]  # stop at next H2
    return list(dict.fromkeys(_ALT_LIST_RE.findall(section)))  # de-dup, preserve order


def write_catalog(catalog: dict[str, Any] | None = None,
                  out_path: Path | None = None) -> Path:
    catalog = catalog if catalog is not None else build_catalog()
    out_path = out_path or (vault_root() / "graph" / "tool-catalog.yaml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    return out_path


# --------------------------------------------------------------------------
# cheatsheet rendering
# --------------------------------------------------------------------------

CHEATSHEET_HEADER = """# Tool cheatsheet

Auto-generated from `vault/skills/active/tools/*.md`. Run `agent-os catalog`
to refresh. Authoritative source: the per-tool SKILL.md files.

| Tool | Tier | Category | Cost | Risk | Use when |
|---|---|---|---|---|---|
"""


def render_cheatsheet(catalog: dict[str, Any] | None = None) -> str:
    catalog = catalog if catalog is not None else build_catalog()
    rows = []
    for name in sorted(catalog["tools"]):
        t = catalog["tools"][name]
        desc = (t.get("description") or "").replace("\n", " ").strip()
        if len(desc) > 100:
            desc = desc[:97].rstrip() + "…"
        rows.append(
            f"| `{name}` | {t.get('tier', '?')} | "
            f"{t.get('category', '?')} | {t.get('cost_class', '?')} | "
            f"{t.get('risk_class', '?')} | {desc} |"
        )
    return CHEATSHEET_HEADER + "\n".join(rows) + "\n"


def write_cheatsheets(catalog: dict[str, Any] | None = None) -> dict[str, Path]:
    """Write the agent-facing cheatsheet (vault) AND the human one (docs)."""
    catalog = catalog if catalog is not None else build_catalog()
    rendered = render_cheatsheet(catalog)
    agent_path = vault_root() / "skills" / "active" / "tools" / "_catalog.md"
    docs_path = repo_root() / "docs" / "tool-cheatsheet.md"
    for path in (agent_path, docs_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered)
    return {"agent": agent_path, "docs": docs_path}


# --------------------------------------------------------------------------
# CLI helpers
# --------------------------------------------------------------------------

def regenerate_all() -> dict[str, Any]:
    """One-shot: rebuild catalog + cheatsheets. Returns a summary."""
    catalog = build_catalog()
    yaml_path = write_catalog(catalog)
    cheats = write_cheatsheets(catalog)
    return {
        "catalog": str(yaml_path),
        "cheatsheet_agent": str(cheats["agent"]),
        "cheatsheet_docs": str(cheats["docs"]),
        "tools": len(catalog["tools"]),
        "bundles": len(catalog["bundles"]),
        "models": len(catalog["models"]),
    }


def show_tool(name: str) -> str:
    """Return the raw SKILL.md content for a tool, or a 'not found' message."""
    skill_path = vault_root() / "skills" / "active" / "tools" / f"{name}.md"
    if not skill_path.exists():
        return f"# Tool not found: {name}\n\nKnown tools: {', '.join(sorted(load_skills()))}"
    return skill_path.read_text()


def list_models() -> dict[str, Any]:
    return load_models()


if __name__ == "__main__":
    import json
    print(json.dumps(regenerate_all(), indent=2))
