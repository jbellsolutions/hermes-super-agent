"""Pluggable customizer protocol — the brain of the build flow.

A customizer takes a fresh OpenSwarm clone and reshapes it for a business
purpose. Three implementations ship:

- ``noop``   — leave the clone untouched. The "default" swarm uses this.
                 Also the test default.
- ``manual`` — apply a deterministic spec (append context to instructions,
                 update business_purpose). No LLM. Cheap and offline.
- ``claude_code`` — shell out to ``claude --print`` against the swarm folder
                      with AGENTS.md + the description as context. Real LLM.

The protocol is intentionally narrow so a future ``claude_subagents`` runtime
(currently a stub) can be dropped in by writing one more class.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class BuildContext:
    name: str
    description: str
    swarm_dir: Path
    agents_md: str  # contents of vendor's AGENTS.md, fed to LLM customizers


@dataclass
class CustomizationOutcome:
    success: bool
    summary: str = ""
    agents: list[dict[str, Any]] = field(default_factory=list)
    output_types: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    patches_diff: str | None = None
    error: str | None = None


class Customizer(Protocol):
    name: str

    def customize(self, ctx: BuildContext) -> CustomizationOutcome: ...


# --------------------------------------------------------------------------
# noop
# --------------------------------------------------------------------------

class NoopCustomizer:
    name = "noop"

    def customize(self, ctx: BuildContext) -> CustomizationOutcome:
        return CustomizationOutcome(
            success=True,
            summary="no changes — vendor clone passed through",
            agents=[],
            output_types=[],
            examples=[],
        )


# --------------------------------------------------------------------------
# manual — deterministic spec
# --------------------------------------------------------------------------

class ManualCustomizer:
    """Apply a structured spec without invoking any LLM.

    Spec shape::

        {
            "shared_context": "you are an SEO swarm. ...",  # appended verbatim
            "agents": [
                {
                    "name": "deep_research",          # folder to target
                    "role": "...",
                    "instructions_append": "Optional extra context block.",
                },
                ...
            ],
            "output_types": ["blog_post_md"],
            "examples": ["Write me 3 SEO posts about X."],
        }

    Folders are NOT renamed — that requires invasive edits to swarm.py and the
    agent module imports. Callers who need rename-style restructuring should
    use the claude_code customizer.
    """

    name = "manual"

    def __init__(self, spec: dict[str, Any] | None = None) -> None:
        self.spec = spec or {}

    def customize(self, ctx: BuildContext) -> CustomizationOutcome:
        spec = self.spec
        try:
            shared_context = spec.get("shared_context") or self._auto_shared_context(ctx)
            self._append_shared_instructions(ctx.swarm_dir, shared_context)

            agents_out: list[dict[str, Any]] = []
            for agent_spec in spec.get("agents", []):
                folder = ctx.swarm_dir / agent_spec["name"]
                if not folder.exists():
                    continue
                if agent_spec.get("instructions_append"):
                    self._append_agent_instructions(folder, agent_spec["instructions_append"])
                agents_out.append({
                    "name": agent_spec["name"],
                    "role": agent_spec.get("role", ""),
                    "tools": agent_spec.get("tools", []),
                })

            return CustomizationOutcome(
                success=True,
                summary=f"applied manual spec — {len(agents_out)} agents touched",
                agents=agents_out,
                output_types=spec.get("output_types", []),
                examples=spec.get("examples", []),
            )
        except Exception as e:  # noqa: BLE001
            return CustomizationOutcome(
                success=False,
                error=f"{type(e).__name__}: {e}",
            )

    @staticmethod
    def _auto_shared_context(ctx: BuildContext) -> str:
        return textwrap.dedent(f"""
            ## {ctx.name} swarm context

            This swarm has been customized for the following purpose:

            {ctx.description}

            All agents should keep this purpose in mind when producing deliverables.
        """).strip() + "\n"

    @staticmethod
    def _append_shared_instructions(swarm_dir: Path, block: str) -> None:
        path = swarm_dir / "shared_instructions.md"
        existing = path.read_text() if path.exists() else ""
        marker = "<!-- agent-os: customization -->"
        if marker in existing:
            # Replace prior block to keep idempotent.
            head, _, _ = existing.partition(marker)
            existing = head.rstrip() + "\n"
        with path.open("w") as fh:
            fh.write(existing.rstrip() + f"\n\n{marker}\n{block}\n")

    @staticmethod
    def _append_agent_instructions(agent_folder: Path, block: str) -> None:
        path = agent_folder / "instructions.md"
        existing = path.read_text() if path.exists() else ""
        marker = "<!-- agent-os: customization -->"
        if marker in existing:
            head, _, _ = existing.partition(marker)
            existing = head.rstrip() + "\n"
        with path.open("w") as fh:
            fh.write(existing.rstrip() + f"\n\n{marker}\n{block}\n")


# --------------------------------------------------------------------------
# claude_code — shell out to the claude CLI
# --------------------------------------------------------------------------

CLAUDE_PROMPT_TEMPLATE = """You are customizing an OpenSwarm clone into a {name} swarm.

# Goal
{description}

# How to customize
Read AGENTS.md (already in your context — it's authoritative). Edit the agent
folders, prompts, and shared_instructions.md to specialize this swarm for the
goal. Do not add new infrastructure or new top-level files. Keep swarm.py
runnable — if you rename agent folders, update the imports in swarm.py
accordingly.

# Output expectations
When you're done, write a JSON summary to ``.build/customizer_report.json``
inside the swarm folder with this shape:
{{
  "agents": [{{ "name": "<folder name>", "role": "<one line>", "tools": [] }}, ...],
  "output_types": ["<artifact type>", ...],
  "examples": ["<example user prompt>", ...]
}}

# AGENTS.md (verbatim from the upstream)
{agents_md}
"""


class ClaudeCodeCustomizer:
    """Invoke the local ``claude`` CLI in print mode against the swarm folder.

    Requires ``claude`` on PATH and a configured Anthropic auth. Uses a fresh
    git history inside the swarm folder so we can capture customization as a
    diff for upgrade replay.
    """

    name = "claude_code"

    def __init__(
        self,
        *,
        timeout_s: float = 1800.0,
        cost_budget_usd: float = 5.0,
        claude_bin: str | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.cost_budget_usd = cost_budget_usd
        self.claude_bin = claude_bin or os.environ.get("CLAUDE_BIN", "claude")

    def customize(self, ctx: BuildContext) -> CustomizationOutcome:
        if shutil.which(self.claude_bin) is None:
            return CustomizationOutcome(
                success=False,
                error=f"claude CLI not found ({self.claude_bin!r}). "
                "Install it or pass a different customizer.",
            )

        # Pin a baseline so we can diff the customization.
        try:
            self._git_init_baseline(ctx.swarm_dir)
        except subprocess.SubprocessError as e:
            return CustomizationOutcome(
                success=False,
                error=f"git baseline init failed: {e}",
            )

        prompt = CLAUDE_PROMPT_TEMPLATE.format(
            name=ctx.name,
            description=ctx.description,
            agents_md=ctx.agents_md or "(AGENTS.md not found in vendor)",
        )
        cmd = [
            self.claude_bin,
            "--print",
            "--add-dir", str(ctx.swarm_dir),
            "--allowed-tools", "Read,Edit,Write,Bash",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(ctx.swarm_dir),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CustomizationOutcome(
                success=False,
                error=f"claude exceeded {self.timeout_s}s timeout",
            )

        if proc.returncode != 0:
            return CustomizationOutcome(
                success=False,
                error=f"claude exit {proc.returncode}: {proc.stderr[:500]}",
            )

        report = self._read_report(ctx.swarm_dir)
        diff = self._capture_diff(ctx.swarm_dir)

        return CustomizationOutcome(
            success=True,
            summary=proc.stdout[-1000:].strip() or "claude completed",
            agents=report.get("agents", []),
            output_types=report.get("output_types", []),
            examples=report.get("examples", []),
            patches_diff=diff,
        )

    @staticmethod
    def _git_init_baseline(swarm_dir: Path) -> None:
        # git init only if not already a repo.
        if (swarm_dir / ".git").exists():
            return
        env = {**os.environ, "GIT_AUTHOR_NAME": "agent-os", "GIT_AUTHOR_EMAIL": "agent-os@local",
               "GIT_COMMITTER_NAME": "agent-os", "GIT_COMMITTER_EMAIL": "agent-os@local"}
        subprocess.run(["git", "init", "-q"], cwd=swarm_dir, check=True, env=env)
        subprocess.run(["git", "add", "-A"], cwd=swarm_dir, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "agent-os: pre-customization baseline"],
            cwd=swarm_dir, check=True, env=env,
        )

    @staticmethod
    def _capture_diff(swarm_dir: Path) -> str | None:
        try:
            out = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=swarm_dir, capture_output=True, text=True, check=False,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
        return out.stdout or None

    @staticmethod
    def _read_report(swarm_dir: Path) -> dict[str, Any]:
        import json
        report_path = swarm_dir / ".build" / "customizer_report.json"
        if not report_path.exists():
            return {}
        try:
            return json.loads(report_path.read_text())
        except (OSError, ValueError):
            return {}


# --------------------------------------------------------------------------
# factory
# --------------------------------------------------------------------------

def get_customizer(spec: str | dict[str, Any] | Customizer | None,
                   *, options: dict[str, Any] | None = None) -> Customizer:
    """Resolve a customizer name or instance to a concrete customizer.

    - ``None`` or ``"noop"`` → NoopCustomizer
    - ``"manual"`` → ManualCustomizer(options or {})
    - ``"claude_code"`` → ClaudeCodeCustomizer(**(options or {}))
    - dict → treated as ManualCustomizer(spec=dict)
    - already a Customizer → returned as-is
    """
    if spec is None or spec == "noop":
        return NoopCustomizer()
    if isinstance(spec, str):
        if spec == "manual":
            return ManualCustomizer(options or {})
        if spec == "claude_code":
            return ClaudeCodeCustomizer(**(options or {}))
        raise ValueError(f"unknown customizer: {spec!r}")
    if isinstance(spec, dict):
        return ManualCustomizer(spec)
    if hasattr(spec, "customize"):
        return spec  # already a Customizer
    raise TypeError(f"can't coerce {spec!r} to a Customizer")
