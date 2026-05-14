#!/usr/bin/env python3
"""Super Agent installer — saiyan (lite) or super-saiyan (full).

Single-file, stdlib-only. Designed to be invoked from a Claude Code /
Codex / Cursor session running the master prompt in INSTALL.md, but
runnable by hand too.

Usage:
    python3 install.py --mode=saiyan       [--target=PATH] [--dry-run] [--force]
    python3 install.py --mode=super-saiyan
    python3 install.py --mode=lite          # alias for saiyan
    python3 install.py --mode=full          # alias for super-saiyan

Saiyan (lite): copies the planner + 14 in-process runtimes + 16 SKILL.md
files into the target project. No new infrastructure. ~3 minutes.

Super-saiyan (full): runs scripts/setup.sh + scripts/deploy.sh from this
repo to bring up the full Railway fabric. ~30 minutes.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent

# Pure-skills surface — copied verbatim by saiyan mode.
# (relative_source, relative_target) — target is relative to target_root + agent_os layout.
_ORCH_PURE = [
    "__init__.py",
    "tier_classifier.py",
    "tool_planner.py",
    "model_planner.py",
    "plan_card.py",
    "intent_classifier.py",
    "catalog.py",
]

_ADAPTERS_PURE = [
    "__init__.py",
    "job_router.py",
    "plan_overrides.py",
    "vault_memory.py",
]

_PURE_RUNTIMES = [
    "agent_zero", "aider", "browser_use", "claude_managed", "claude_subagents",
    "codex_cli", "computer_use", "e2b", "exa", "hermes_self",
    "livekit", "openclaw", "openswarm", "terminal",
]

_PURE_SKILL_MD = [
    "_catalog.md", "agent_zero.md", "aider.md", "browser_use.md",
    "claude_managed.md", "claude_subagents.md", "codex_cli.md", "composio.md",
    "computer_use.md", "e2b.md", "exa.md", "hermes_self.md", "livekit.md",
    "openclaw.md", "openswarm.md", "terminal.md",
]

# Saiyan mode runtime registry — what dispatch() should know about.
_SAIYAN_RUNTIMES = sorted(_PURE_RUNTIMES)

# Minimal deps for saiyan mode (no fabric).
_SAIYAN_DEPS = [
    "pyyaml>=6.0",
    "httpx>=0.27",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--mode", required=True,
                   choices=["saiyan", "super-saiyan", "lite", "full"])
    p.add_argument("--target", default=None,
                   help="Target project root (default: current working dir).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would happen, write nothing.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing files in the target.")
    args = p.parse_args(argv)

    mode = "saiyan" if args.mode in ("saiyan", "lite") else "super-saiyan"

    if mode == "super-saiyan":
        return _super_saiyan()

    target = Path(args.target or os.getcwd()).resolve()
    return _saiyan(target=target, dry_run=args.dry_run, force=args.force)


# ---------------------------------------------------------------------------
# Saiyan mode (lite)
# ---------------------------------------------------------------------------

def _saiyan(*, target: Path, dry_run: bool, force: bool) -> int:
    print(f"\n⚡ Super Agent — Saiyan install → {target}\n")

    if sys.version_info < (3, 11):
        print(f"✗ Python 3.11+ required (you have {sys.version_info.major}."
              f"{sys.version_info.minor}).")
        return 2

    if not target.exists():
        print(f"✗ Target {target} does not exist. Create it or pass --target.")
        return 2

    layout = _detect_layout(target)
    target_agent_os = target / layout / "agent_os"
    target_vault = target / "vault" / "skills" / "active" / "tools"

    print(f"  layout:        {layout}/agent_os/...")
    print(f"  agent_os →     {target_agent_os}")
    print(f"  vault/skills → {target_vault}")
    print(f"  dry-run:       {dry_run}")
    print(f"  force:         {force}")
    print()

    plan = _build_copy_plan(target_agent_os, target_vault)

    conflicts = [t for _, t in plan if t.exists() and not _identical(_, t)]
    if conflicts and not force:
        print(f"✗ {len(conflicts)} target files would be overwritten with different "
              f"content:")
        for c in conflicts[:10]:
            print(f"    {c}")
        if len(conflicts) > 10:
            print(f"    ... and {len(conflicts) - 10} more")
        print(f"\n  Re-run with --force to overwrite, or --dry-run to inspect.")
        return 3

    # Copy
    for src, tgt in plan:
        if dry_run:
            verb = "WOULD UPDATE" if tgt.exists() else "WOULD CREATE"
            print(f"  {verb}  {tgt}")
            continue
        tgt.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, tgt)

    if not dry_run:
        # Patch the copied job_router.py for lite-mode dispatch.
        _patch_job_router_for_saiyan(target_agent_os / "orchestrator" / "adapters" / "job_router.py")
        # Merge deps.
        _merge_deps(target=target, dry_run=dry_run)
        # Smoke test.
        ok = _smoke_test(target=target, layout=layout)
        if not ok:
            print("\n✗ Smoke test failed. See output above.")
            return 4

    print()
    if dry_run:
        print(f"  dry-run complete: {len(plan)} files would be written.")
    else:
        print(f"✓ saiyan install complete: {len(plan)} files written.\n")
        _print_next_steps()
    return 0


def _detect_layout(target: Path) -> str:
    """Return 'src' if target uses src/agent_os/ layout, else '.' (flat)."""
    if (target / "src" / "agent_os").exists():
        return "src"
    if (target / "agent_os").exists():
        return "."
    # No existing agent_os/ — pick a default based on whether there's a src/ dir.
    return "src" if (target / "src").exists() else "."


def _build_copy_plan(target_agent_os: Path, target_vault: Path) -> list[tuple[Path, Path]]:
    """Return [(source, target)] pairs for all files to copy in saiyan mode."""
    pairs: list[tuple[Path, Path]] = []

    src_orch = SCRIPT_DIR / "src" / "agent_os" / "orchestrator"
    tgt_orch = target_agent_os / "orchestrator"
    for f in _ORCH_PURE:
        pairs.append((src_orch / f, tgt_orch / f))
    for f in _ADAPTERS_PURE:
        pairs.append((src_orch / "adapters" / f, tgt_orch / "adapters" / f))

    # Configs (yaml + identities/*.yaml)
    pairs.append((src_orch / "config" / "models.yaml", tgt_orch / "config" / "models.yaml"))
    pairs.append((src_orch / "config" / "tiers.yaml", tgt_orch / "config" / "tiers.yaml"))
    identities_dir = src_orch / "config" / "identities"
    if identities_dir.exists():
        for ident in sorted(identities_dir.glob("*.yaml")):
            pairs.append((ident, tgt_orch / "config" / "identities" / ident.name))

    # Runtimes — _base.py + 14 pure runtime dirs (every .py and .yaml inside)
    src_rt = SCRIPT_DIR / "src" / "agent_os" / "runtimes"
    tgt_rt = target_agent_os / "runtimes"
    base_py = src_rt / "_base.py"
    if base_py.exists():
        pairs.append((base_py, tgt_rt / "_base.py"))
    init_py = src_rt / "__init__.py"
    if init_py.exists():
        pairs.append((init_py, tgt_rt / "__init__.py"))
    for runtime in _PURE_RUNTIMES:
        rt_src = src_rt / runtime
        rt_tgt = tgt_rt / runtime
        if not rt_src.exists():
            continue
        for f in sorted(rt_src.rglob("*")):
            if f.is_dir() or f.name == "__pycache__" or "__pycache__" in f.parts:
                continue
            if f.suffix not in (".py", ".yaml", ".md"):
                continue
            rel = f.relative_to(rt_src)
            pairs.append((f, rt_tgt / rel))

    # 16 SKILL.md files
    src_tools = SCRIPT_DIR / "vault" / "skills" / "active" / "tools"
    for md in _PURE_SKILL_MD:
        src_md = src_tools / md
        if src_md.exists():
            pairs.append((src_md, target_vault / md))

    # Top-level agent_os/__init__.py shim if target doesn't have one
    target_init = target_agent_os / "__init__.py"
    if not target_init.exists():
        pairs.append((SCRIPT_DIR / "src" / "agent_os" / "__init__.py", target_init))

    return pairs


def _identical(src: Path, tgt: Path) -> bool:
    try:
        return src.read_bytes() == tgt.read_bytes()
    except Exception:
        return False


def _patch_job_router_for_saiyan(router_path: Path) -> None:
    """Trim runtime registries in the copied job_router.py to lite-only set
    and rewrite the unknown-runtime error to point at super-saiyan."""
    if not router_path.exists():
        return
    text = router_path.read_text()

    # Remove fabric runtimes from KNOWN_RUNTIMES via the dicts that feed it.
    # Strategy: replace the literal _ASYNC_RUNTIMES / _SYNC_RUNTIMES dicts with
    # saiyan-only versions, leaving everything else (route(), Job, dispatch)
    # untouched.
    saiyan_async = '_ASYNC_RUNTIMES = {\n}\n'  # no async runtimes in lite mode
    saiyan_sync = (
        "_SYNC_RUNTIMES = {\n"
        + "\n".join(
            f'    "{r}": "agent_os.runtimes.{r}.invoke",'
            for r in _SAIYAN_RUNTIMES
        )
        + "\n}\n"
    )

    text = re.sub(
        r"_ASYNC_RUNTIMES = \{[^}]*\}\s*\n",
        saiyan_async,
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"_SYNC_RUNTIMES = \{[^}]*\}\s*\n",
        saiyan_sync,
        text,
        count=1,
        flags=re.DOTALL,
    )

    # Rewrite "Unknown runtime" error message to point at super-saiyan.
    text = text.replace(
        'raise ValueError(f"Unknown runtime: {runtime}")',
        'raise RuntimeError(\n'
        '        f"runtime {runtime!r} needs the super-saiyan fabric layer "\n'
        '        "(NATS + Temporal + Coordinator + spawner). Re-run install.py "\n'
        '        "with --mode=super-saiyan, or install the full fabric: "\n'
        '        "https://github.com/jbellsolutions/hermes-super-agent"\n'
        '    )',
    )

    # Mark the file with a saiyan banner so it's obvious this was patched.
    if "saiyan-mode patched" not in text:
        text = (
            "# saiyan-mode patched: fabric runtimes (a2a_delegate, coordinator,\n"
            "# retell_channel, vps_spawn) are NOT registered here. Asking the\n"
            "# planner to dispatch one raises a friendly RuntimeError pointing\n"
            "# at super-saiyan mode.\n"
            + text
        )

    router_path.write_text(text)


def _merge_deps(*, target: Path, dry_run: bool) -> None:
    """Merge saiyan deps into target's pyproject.toml or requirements.txt.

    Idempotent: if our deps are already declared, no-op.
    """
    pyproject = target / "pyproject.toml"
    reqs = target / "requirements.txt"

    if pyproject.exists():
        text = pyproject.read_text()
        added = []
        for dep in _SAIYAN_DEPS:
            pkg = dep.split(">=")[0].split("==")[0].split("[")[0].strip().lower()
            # Skip if any line in the [project] table mentions this pkg
            if re.search(rf'["\']?{re.escape(pkg)}["\[\>\=]', text, flags=re.IGNORECASE):
                continue
            added.append(dep)
        if added:
            print(f"  merging {len(added)} dep(s) into pyproject.toml")
            # Best-effort append into [project] dependencies = [...]
            new = re.sub(
                r"(dependencies\s*=\s*\[)([^\]]*)\]",
                lambda m: m.group(0).rstrip("]")
                + ("    \"" + "\",\n    \"".join(added) + "\",\n]"),
                text,
                count=1,
            )
            if new != text and not dry_run:
                pyproject.write_text(new)
        else:
            print("  pyproject.toml already has saiyan deps — skipping.")
        return

    # Fall back to requirements.txt
    existing = reqs.read_text() if reqs.exists() else ""
    added_lines = [d for d in _SAIYAN_DEPS
                   if d.split(">=")[0].split("==")[0].lower() not in existing.lower()]
    if added_lines and not dry_run:
        with reqs.open("a") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("# Super Agent saiyan deps\n")
            for d in added_lines:
                fh.write(d + "\n")
        print(f"  appended {len(added_lines)} dep(s) to requirements.txt")


def _smoke_test(*, target: Path, layout: str) -> bool:
    """Import tool_planner.plan from the target and run a one-line plan.

    Soft on missing third-party deps: if pyyaml or another dep isn't
    installed in the user's Python yet, we still consider the install
    successful (the files copied correctly) and print instructions for
    installing deps.
    """
    pythonpath = str(target / layout) if layout == "src" else str(target)
    code = (
        "from agent_os.orchestrator.adapters.job_router import Job\n"
        "from agent_os.orchestrator.tool_planner import plan\n"
        "p = plan(Job(prompt='hi', tags=set()))\n"
        "print(f'OK primary_tool={p.primary_tool} tier={p.tier}')\n"
    )
    print("  smoke test:")
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath + os.pathsep + env.get("PYTHONPATH", "")
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=target, env=env, capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:
        print(f"    ✗ failed to invoke smoke test: {exc}")
        return False

    output = (result.stdout + result.stderr).strip()

    # ModuleNotFoundError is "you haven't pip-installed yet" — that's a
    # follow-up step, not an install failure. Files are on disk; deps are
    # listed in your pyproject.toml / requirements.txt.
    if "ModuleNotFoundError" in output:
        missing = re.search(r"No module named ['\"]([^'\"]+)['\"]", output)
        modname = missing.group(1) if missing else "<unknown>"
        print(f"    ⚠ Files copied OK, but Python module {modname!r} isn't "
              "installed yet.")
        print("    Run `pip install -r requirements.txt` (or `uv sync` if you")
        print("    use uv) in your project root, then re-run the smoke test:")
        print()
        print("        python -c \"from agent_os.orchestrator.tool_planner "
              "import plan; \\")
        print("                   from agent_os.orchestrator.adapters."
              "job_router import Job; \\")
        print("                   p = plan(Job(prompt='hi', tags=set())); \\")
        print("                   print('OK', p.primary_tool, p.tier)\"")
        return True  # install itself succeeded

    print("    " + (result.stdout.strip() or result.stderr.strip()))
    return result.returncode == 0


def _print_next_steps() -> None:
    print(
        "Next steps — wire it into your Super Agent turn handler:\n"
        "\n"
        "  from agent_os.orchestrator import intent_classifier\n"
        "  from agent_os.orchestrator.adapters.job_router import Job, dispatch\n"
        "  from agent_os.orchestrator.tool_planner import plan\n"
        "  from agent_os.orchestrator.plan_card import render\n"
        "\n"
        "  intent = intent_classifier.classify(user_text)\n"
        "  job = Job(prompt=user_text, tags=set(intent.tags))\n"
        "  tool_plan = plan(job, identity='primary_hermes')\n"
        "  print(render(tool_plan))   # show plan card\n"
        "  # await user yes / YES / cancel...\n"
        "  result = await dispatch(job, plan=tool_plan)\n"
        "\n"
        "Docs: https://github.com/jbellsolutions/hermes-super-agent/blob/main/docs/modes.md\n"
    )


# ---------------------------------------------------------------------------
# Super-saiyan mode (full)
# ---------------------------------------------------------------------------

def _super_saiyan() -> int:
    """Delegate to scripts/setup.sh + scripts/deploy.sh — the existing path."""
    setup = SCRIPT_DIR / "scripts" / "setup.sh"
    deploy = SCRIPT_DIR / "scripts" / "deploy.sh"
    if not setup.exists() or not deploy.exists():
        print("✗ scripts/setup.sh or scripts/deploy.sh missing. Are you running "
              "install.py from the hermes-super-agent repo root?")
        return 2

    print("\n🟡 Super Agent — Super Saiyan install — full Railway fabric.\n")
    print("  This runs: scripts/setup.sh (interactive credentials)")
    print("            scripts/deploy.sh (Railway deploy of 5 services)")
    print()

    rc = subprocess.call(["bash", str(setup)])
    if rc != 0:
        return rc
    return subprocess.call(["bash", str(deploy)])


if __name__ == "__main__":
    sys.exit(main())
