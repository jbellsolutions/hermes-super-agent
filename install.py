#!/usr/bin/env python3
"""Hermes Super Agent installer — saiyan (lite), kaioken (local fabric), super-saiyan-5 (cloud).

Single-file, stdlib-only. Designed to be invoked from a Claude Code /
Codex / Cursor session running the master prompt in INSTALL.md, but
runnable by hand too.

USAGE
=====

  python3 install.py --mode=saiyan           [--target=PATH] [--dry-run] [--force] [--yes]
                                             [--check] [--update] [--uninstall]
                                             [--identities=primary_hermes,coo,...]
  python3 install.py --mode=kaioken          [--yes] [--telegram]
  python3 install.py --mode=super-saiyan-5

ALIASES
=======

  lite          → saiyan
  full          → super-saiyan-5
  super-saiyan  → super-saiyan-5   (old name, kept for backward compat)

MODES
=====

  saiyan         — drop the planner + 14 in-process runtimes + 16 skills
                   into an existing project. ~3 min, $0 infra.

  kaioken        — full local Hermes fabric in Docker (NATS + Temporal +
                   Coordinator + Admiral). Spawns Tier 2 superagents as
                   sibling Docker containers. ~10 min, $0 infra, Docker required.

  super-saiyan-5 — full Railway control plane + DigitalOcean Tier 2
                   spawning. Always-on, public A2A endpoint, team-shared.
                   ~30 min, ~$45/mo floor + per-spawn.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent

# Pure-skills surface — copied verbatim by saiyan mode.
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
    "saiyan_overrides.py",   # NEW — replaces the old regex patch
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

# Default identity for saiyan installs. Override with --identities.
_DEFAULT_IDENTITIES = ["primary_hermes"]

# Minimal deps for saiyan mode (no fabric).
_SAIYAN_DEPS = [
    "pyyaml>=6.0",
    "httpx>=0.27",
]

# Stamp prefix that survives `--check` / `--update` / `--uninstall`. The
# *marker* (the bit that identifies a line as ours) is stamp-agnostic — both
# `# saiyan-installed: ...` (Python/YAML) and `<!-- saiyan-installed: ... -->`
# (Markdown) get recognized via the bare _STAMP_MARKER.
_STAMP_MARKER = "saiyan-installed:"
_STAMP_PREFIX = f"# {_STAMP_MARKER}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__.split("\n\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--mode", required=True,
                   choices=["saiyan", "kaioken", "super-saiyan-5",
                            "lite", "full", "super-saiyan"])
    p.add_argument("--target", default=None,
                   help="Target project root for saiyan mode (default: cwd).")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would happen, write nothing.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing files in the target.")
    p.add_argument("--yes", action="store_true",
                   help="Skip confirmation prompts (e.g. pip install).")
    p.add_argument("--check", action="store_true",
                   help="(saiyan) report drift between installed copies and upstream; write nothing.")
    p.add_argument("--update", action="store_true",
                   help="(saiyan) re-run copy, refreshing stamped files. Skips files the user has modified locally unless --force.")
    p.add_argument("--uninstall", action="store_true",
                   help="(saiyan) remove every stamped file (with confirmation).")
    p.add_argument("--identities", default=",".join(_DEFAULT_IDENTITIES),
                   help="(saiyan) comma-separated identity packs to install. "
                        "Use --identities=list to print available identities and exit. "
                        "Use --identities=all to install everything.")
    p.add_argument("--telegram", action="store_true",
                   help="(kaioken) also start the Telegram bot sidecar.")
    args = p.parse_args(argv)

    mode = _canonical_mode(args.mode)

    if mode == "super-saiyan-5":
        return _super_saiyan_5()
    if mode == "kaioken":
        return _kaioken(yes=args.yes, telegram=args.telegram)

    # saiyan
    target = Path(args.target or os.getcwd()).resolve()
    if args.identities.strip().lower() == "list":
        return _list_identities()
    identities = _parse_identities(args.identities)

    if args.check:
        return _saiyan_check(target=target)
    if args.uninstall:
        return _saiyan_uninstall(target=target, yes=args.yes)
    return _saiyan(
        target=target,
        dry_run=args.dry_run,
        # --update refreshes stamped (ours) files but does NOT overwrite
        # user-modified unstamped files unless --force is also passed.
        force=args.force,
        yes=args.yes,
        identities=identities,
        is_update=args.update,
    )


def _canonical_mode(raw: str) -> str:
    if raw in ("saiyan", "lite"):
        return "saiyan"
    if raw == "kaioken":
        return "kaioken"
    return "super-saiyan-5"   # super-saiyan-5, full, super-saiyan all map here


# ---------------------------------------------------------------------------
# Saiyan mode (lite)
# ---------------------------------------------------------------------------

def _saiyan(
    *,
    target: Path,
    dry_run: bool,
    force: bool,
    yes: bool,
    identities: list[str],
    is_update: bool,
) -> int:
    label = "saiyan-mode update" if is_update else "saiyan-mode install"
    print(f"\n⚡ Hermes {label} → {target}\n")

    if sys.version_info < (3, 11):
        print(f"✗ Python 3.11+ required (you have "
              f"{sys.version_info.major}.{sys.version_info.minor}).")
        return 2
    if not target.exists():
        print(f"✗ Target {target} does not exist. Create it or pass --target.")
        return 2

    layout = _detect_layout(target)
    target_agent_os = target / layout / "agent_os"
    target_vault = target / "vault" / "skills" / "active" / "tools"

    print(f"  layout:       {layout}/agent_os/...")
    print(f"  agent_os →    {target_agent_os}")
    print(f"  vault/skills →{target_vault}")
    print(f"  identities:   {', '.join(identities)}")
    print(f"  dry-run:      {dry_run}   force: {force}   yes: {yes}\n")

    plan = _build_copy_plan(target_agent_os, target_vault, identities=identities)

    # Conflict detection: skip files that already exist with the same content,
    # warn-and-skip user-modified files unless --force.
    conflicts = []
    for src, tgt in plan:
        if not tgt.exists():
            continue
        if _identical_ignoring_stamp(src, tgt):
            continue
        # If the target has our stamp, it's safe to refresh (we wrote it last).
        if _has_stamp(tgt):
            continue
        conflicts.append(tgt)

    if conflicts and not force:
        print(f"✗ {len(conflicts)} target file(s) would be overwritten with "
              f"different content (and they're not stamped as ours):")
        for c in conflicts[:10]:
            print(f"    {c}")
        if len(conflicts) > 10:
            print(f"    ... and {len(conflicts) - 10} more")
        print("\n  Re-run with --force to overwrite, --dry-run to inspect.")
        return 3

    # Copy + stamp
    sha = _repo_sha()
    stamp = f"{_STAMP_PREFIX} hermes-super-agent@{sha} on {_today()}"
    written = 0
    for src, tgt in plan:
        if dry_run:
            verb = "WOULD UPDATE" if tgt.exists() else "WOULD CREATE"
            print(f"  {verb}  {tgt}")
            continue
        tgt.parent.mkdir(parents=True, exist_ok=True)
        _copy_with_stamp(src, tgt, stamp=stamp)
        written += 1

    if not dry_run:
        # Wire saiyan_overrides into the copied adapters/__init__.py so it
        # runs every time the user imports agent_os.orchestrator.adapters.
        _wire_saiyan_overrides(target_agent_os / "orchestrator" / "adapters" / "__init__.py")
        # Merge deps (and offer to install them).
        _merge_deps(target=target, yes=yes)
        # Stage the example so the user has a working demo.
        _copy_example(target, "saiyan_hello.py", stamp=stamp)
        # Real smoke test.
        ok = _smoke_test_saiyan(target=target, layout=layout)
        if not ok:
            print("\n✗ Smoke test failed. See output above.")
            return 4

    print()
    if dry_run:
        print(f"  dry-run complete: {len(plan)} files would be written.")
    else:
        print(f"✓ saiyan {'updated' if is_update else 'install complete'}: "
              f"{written} files written.\n")
        _print_next_steps()
    return 0


def _detect_layout(target: Path) -> str:
    if (target / "src" / "agent_os").exists():
        return "src"
    if (target / "agent_os").exists():
        return "."
    return "src" if (target / "src").exists() else "."


def _list_identities() -> int:
    src = SCRIPT_DIR / "src" / "agent_os" / "orchestrator" / "config" / "identities"
    if not src.exists():
        print("(no identities/ dir found in upstream)")
        return 1
    print("Available identities:")
    for p in sorted(src.glob("*.yaml")):
        print(f"  {p.stem}")
    print("\nUse --identities=name1,name2 or --identities=all")
    return 0


def _parse_identities(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw or raw.lower() == "all":
        src = SCRIPT_DIR / "src" / "agent_os" / "orchestrator" / "config" / "identities"
        if src.exists():
            return sorted(p.stem for p in src.glob("*.yaml"))
        return list(_DEFAULT_IDENTITIES)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _build_copy_plan(
    target_agent_os: Path,
    target_vault: Path,
    *,
    identities: list[str],
) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    src_orch = SCRIPT_DIR / "src" / "agent_os" / "orchestrator"
    tgt_orch = target_agent_os / "orchestrator"

    for f in _ORCH_PURE:
        pairs.append((src_orch / f, tgt_orch / f))
    for f in _ADAPTERS_PURE:
        src_f = src_orch / "adapters" / f
        if src_f.exists():
            pairs.append((src_f, tgt_orch / "adapters" / f))

    # Configs
    for cfg in ("models.yaml", "tiers.yaml"):
        src_cfg = src_orch / "config" / cfg
        if src_cfg.exists():
            pairs.append((src_cfg, tgt_orch / "config" / cfg))

    identities_dir = src_orch / "config" / "identities"
    if identities_dir.exists():
        wanted = set(identities)
        for ident in sorted(identities_dir.glob("*.yaml")):
            if ident.stem in wanted:
                pairs.append((ident, tgt_orch / "config" / "identities" / ident.name))

    # Runtimes
    src_rt = SCRIPT_DIR / "src" / "agent_os" / "runtimes"
    tgt_rt = target_agent_os / "runtimes"
    for top in ("_base.py", "__init__.py"):
        f = src_rt / top
        if f.exists():
            pairs.append((f, tgt_rt / top))
    for runtime in _PURE_RUNTIMES:
        rt_src = src_rt / runtime
        if not rt_src.exists():
            continue
        for f in sorted(rt_src.rglob("*")):
            if f.is_dir() or "__pycache__" in f.parts:
                continue
            if f.suffix not in (".py", ".yaml", ".md"):
                continue
            rel = f.relative_to(rt_src)
            pairs.append((f, tgt_rt / runtime / rel))

    # 16 SKILL.md files
    src_tools = SCRIPT_DIR / "vault" / "skills" / "active" / "tools"
    for md in _PURE_SKILL_MD:
        src_md = src_tools / md
        if src_md.exists():
            pairs.append((src_md, target_vault / md))

    # Top-level agent_os/__init__.py if target doesn't have one
    target_init = target_agent_os / "__init__.py"
    src_init = SCRIPT_DIR / "src" / "agent_os" / "__init__.py"
    if not target_init.exists() and src_init.exists():
        pairs.append((src_init, target_init))

    return pairs


# ---------------------------------------------------------------------------
# Stamping + file copy
# ---------------------------------------------------------------------------

def _copy_with_stamp(src: Path, tgt: Path, *, stamp: str) -> None:
    """Copy src→tgt, prepending an install stamp for .py/.md/.yaml files."""
    data = src.read_bytes()
    if src.suffix in (".py", ".md", ".yaml", ".yml"):
        stamped = _stamp_text(data.decode("utf-8", errors="replace"), src.suffix, stamp)
        tgt.write_text(stamped)
    else:
        tgt.write_bytes(data)
    try:
        shutil.copymode(src, tgt)
    except OSError:
        pass


def _stamp_text(text: str, suffix: str, stamp: str) -> str:
    """Insert a stamp comment near the top of the file. Idempotent — strips
    any previous stamp first so re-installs don't accumulate banners.

    Suffix-specific placement:
      .py     — after the first blank line (past shebang/docstring/imports header)
      .md     — AFTER the YAML frontmatter (so catalog.parse_skill() still
                sees the `---` block at the very top of the file)
      .yaml   — at the top, as a leading comment
    """
    comment_prefix = "# " if suffix in (".py", ".yaml", ".yml") else "<!-- "
    comment_suffix = "" if suffix in (".py", ".yaml", ".yml") else " -->"
    full_stamp = f"{comment_prefix}{stamp[2:].strip()}{comment_suffix}\n"

    # Strip any existing saiyan-installed banner (the marker appears whether
    # the comment style is `# …` or `<!-- … -->`).
    lines = text.splitlines(keepends=True)
    cleaned = [line for line in lines if _STAMP_MARKER not in line]
    body = "".join(cleaned)

    if suffix == ".py":
        # Insert after the first blank line (past shebang / docstring).
        match = re.search(r"\n\n", body)
        if match:
            return body[:match.end()] + full_stamp + body[match.end():]
        return full_stamp + body

    if suffix == ".md":
        # If the file starts with a YAML frontmatter block, insert the stamp
        # AFTER it so catalog.parse_skill()'s ^---\n…\n---\n regex still
        # matches at byte 0 and the SKILL metadata is preserved.
        fm_match = re.match(r"^---\n.*?\n---\n", body, flags=re.DOTALL)
        if fm_match:
            return body[:fm_match.end()] + full_stamp + body[fm_match.end():]
        return full_stamp + body

    return full_stamp + body


def _has_stamp(path: Path) -> bool:
    if not path.exists() or path.suffix not in (".py", ".md", ".yaml", ".yml"):
        return False
    try:
        head = path.read_text(errors="replace").splitlines()[:20]
    except OSError:
        return False
    return any(_STAMP_MARKER in line for line in head)


def _identical_ignoring_stamp(src: Path, tgt: Path) -> bool:
    try:
        a = src.read_text(errors="replace")
        b = tgt.read_text(errors="replace")
    except OSError:
        return False
    return _strip_stamp(a) == _strip_stamp(b)


def _strip_stamp(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if _STAMP_MARKER not in line
    )


def _wire_saiyan_overrides(adapters_init: Path) -> None:
    """Ensure adapters/__init__.py imports saiyan_overrides and calls apply()."""
    if not adapters_init.exists():
        adapters_init.parent.mkdir(parents=True, exist_ok=True)
        adapters_init.write_text(
            "from . import saiyan_overrides  # saiyan-mode runtime trim\n"
            "saiyan_overrides.apply()\n"
        )
        return
    text = adapters_init.read_text()
    if "saiyan_overrides" in text:
        return
    text = text.rstrip() + (
        "\n\n# saiyan-mode runtime trim — installed by install.py --mode=saiyan\n"
        "from . import saiyan_overrides  # noqa: F401\n"
        "saiyan_overrides.apply()\n"
    )
    adapters_init.write_text(text)


def _copy_example(target: Path, name: str, *, stamp: str) -> None:
    src = SCRIPT_DIR / "examples" / name
    if not src.exists():
        return
    tgt = target / "examples" / name
    tgt.parent.mkdir(parents=True, exist_ok=True)
    _copy_with_stamp(src, tgt, stamp=stamp)
    try:
        tgt.chmod(0o755)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Deps + smoke test
# ---------------------------------------------------------------------------

def _merge_deps(*, target: Path, yes: bool) -> None:
    pyproject = target / "pyproject.toml"
    reqs = target / "requirements.txt"

    if pyproject.exists():
        text = pyproject.read_text()
        added = []
        for dep in _SAIYAN_DEPS:
            pkg = dep.split(">=")[0].split("==")[0].split("[")[0].strip().lower()
            if re.search(rf'["\']?{re.escape(pkg)}["\[\>\=]', text, flags=re.IGNORECASE):
                continue
            added.append(dep)
        if added:
            print(f"  merging {len(added)} dep(s) into pyproject.toml")
            new = re.sub(
                r"(dependencies\s*=\s*\[)([^\]]*)\]",
                lambda m: m.group(0).rstrip("]")
                + ("    \"" + "\",\n    \"".join(added) + "\",\n]"),
                text, count=1,
            )
            if new != text:
                pyproject.write_text(new)
        else:
            print("  pyproject.toml already has saiyan deps — skipping.")
    else:
        # requirements.txt fallback
        existing = reqs.read_text() if reqs.exists() else ""
        added_lines = [
            d for d in _SAIYAN_DEPS
            if d.split(">=")[0].split("==")[0].lower() not in existing.lower()
        ]
        if added_lines:
            with reqs.open("a") as fh:
                if existing and not existing.endswith("\n"):
                    fh.write("\n")
                fh.write("# Hermes saiyan deps\n")
                for d in added_lines:
                    fh.write(d + "\n")
            print(f"  appended {len(added_lines)} dep(s) to requirements.txt")

    # Actually install them. Pick uv if available, else pip.
    if not _yes_or_ask("  Install saiyan deps now?", yes=yes):
        print("  skipped — install yourself when ready:")
        print("    uv sync           # or")
        print("    pip install pyyaml httpx")
        return

    if shutil.which("uv") and pyproject.exists():
        print("  → uv sync")
        rc = subprocess.call(["uv", "sync"], cwd=target)
        if rc != 0:
            print("  ⚠ uv sync exited non-zero — try `pip install -r requirements.txt`")
    else:
        print(f"  → {sys.executable} -m pip install {' '.join(_SAIYAN_DEPS)}")
        rc = subprocess.call(
            [sys.executable, "-m", "pip", "install", *_SAIYAN_DEPS],
            cwd=target,
        )
        if rc != 0:
            print("  ⚠ pip install exited non-zero — review output above")


def _smoke_test_saiyan(*, target: Path, layout: str) -> bool:
    """Run examples/saiyan_hello.py via the user's Python; assert output."""
    example = target / "examples" / "saiyan_hello.py"
    if not example.exists():
        print("  ⚠ examples/saiyan_hello.py not found in target — skipping smoke test")
        return True

    pythonpath = str(target / layout) if layout == "src" else str(target)
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath + os.pathsep + env.get("PYTHONPATH", "")

    sentinel = "hello-from-saiyan-install"
    print(f"  smoke test: examples/saiyan_hello.py --prompt 'echo {sentinel}' --quiet")
    try:
        result = subprocess.run(
            [sys.executable, str(example), "--prompt", f"echo {sentinel}", "--quiet"],
            cwd=target, env=env, capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:
        print(f"    ✗ failed to invoke: {exc}")
        return False

    out = (result.stdout or "") + (result.stderr or "")

    if "ModuleNotFoundError" in out:
        modname_match = re.search(r"No module named ['\"]([^'\"]+)['\"]", out)
        modname = modname_match.group(1) if modname_match else "<unknown>"
        print(f"    ✗ Python module {modname!r} not installed.")
        print(f"    Run `pip install {modname}` (or `uv sync`) and re-run the install.")
        return False

    if result.returncode != 0:
        print(f"    ✗ smoke test exited {result.returncode}")
        for line in (out.strip().splitlines() or [""])[-10:]:
            print(f"      {line}")
        return False
    if sentinel not in out:
        print(f"    ✗ expected output {sentinel!r} not found")
        print(f"      got: {out.strip()[:200]}")
        return False

    print(f"    ✓ {sentinel} returned through the orchestrator")
    return True


def _print_next_steps() -> None:
    print(
        "Next steps — try the demo:\n"
        "\n"
        "  python examples/saiyan_hello.py --prompt 'echo hello'\n"
        "\n"
        "Then wire it into your turn handler:\n"
        "\n"
        "  from agent_os.orchestrator import intent_classifier\n"
        "  from agent_os.orchestrator.adapters.job_router import Job, dispatch\n"
        "  from agent_os.orchestrator.tool_planner import plan\n"
        "  from agent_os.orchestrator.plan_card import render\n"
        "\n"
        "  intent = intent_classifier.classify(user_text)\n"
        "  job = Job(prompt=user_text, tags=set(intent.tags))\n"
        "  tool_plan = plan(job, identity='primary_hermes')\n"
        "  print(render(tool_plan))            # show plan card\n"
        "  result = await dispatch(job, plan=tool_plan)\n"
        "\n"
        "Manage your install:\n"
        "  python3 install.py --mode=saiyan --check         # drift report\n"
        "  python3 install.py --mode=saiyan --update        # refresh from upstream\n"
        "  python3 install.py --mode=saiyan --uninstall     # remove everything\n"
        "\n"
        "Upgrade path:\n"
        "  python3 install.py --mode=kaioken           # local full fabric in Docker\n"
        "  python3 install.py --mode=super-saiyan-5    # cloud always-on fabric\n"
        "\n"
        "Docs: https://github.com/jbellsolutions/hermes-super-agent/blob/main/docs/modes.md\n"
    )


# ---------------------------------------------------------------------------
# Saiyan: --check
# ---------------------------------------------------------------------------

def _saiyan_check(*, target: Path) -> int:
    layout = _detect_layout(target)
    target_agent_os = target / layout / "agent_os"
    target_vault = target / "vault" / "skills" / "active" / "tools"
    plan = _build_copy_plan(target_agent_os, target_vault, identities=_parse_identities("all"))

    missing = []
    drifted = []
    user_modified = []
    in_sync = 0
    for src, tgt in plan:
        if not tgt.exists():
            missing.append(tgt)
            continue
        if _identical_ignoring_stamp(src, tgt):
            in_sync += 1
            continue
        if _has_stamp(tgt):
            # Was ours, upstream changed — needs --update
            drifted.append(tgt)
        else:
            user_modified.append(tgt)

    print(f"\n⚡ saiyan --check → {target}\n")
    print(f"  in sync:       {in_sync}")
    print(f"  drifted:       {len(drifted)} (use --update to refresh)")
    print(f"  user-modified: {len(user_modified)} (use --update --force to overwrite)")
    print(f"  missing:       {len(missing)} (use --update to install)")

    if drifted[:5]:
        print("\n  drifted:")
        for d in drifted[:10]:
            print(f"    {d.relative_to(target)}")
        if len(drifted) > 10:
            print(f"    ... and {len(drifted) - 10} more")

    if user_modified[:5]:
        print("\n  user-modified (preserved):")
        for d in user_modified[:10]:
            print(f"    {d.relative_to(target)}")
        if len(user_modified) > 10:
            print(f"    ... and {len(user_modified) - 10} more")

    return 0 if not (drifted or missing) else 1


# ---------------------------------------------------------------------------
# Saiyan: --uninstall
# ---------------------------------------------------------------------------

def _saiyan_uninstall(*, target: Path, yes: bool) -> int:
    layout = _detect_layout(target)
    target_agent_os = target / layout / "agent_os"
    target_vault = target / "vault" / "skills" / "active" / "tools"
    target_examples = target / "examples"

    candidates: list[Path] = []
    for root in (target_agent_os, target_vault, target_examples):
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if p.is_file() and _has_stamp(p):
                candidates.append(p)

    print(f"\n⚡ saiyan --uninstall → {target}")
    print(f"  Found {len(candidates)} stamped file(s).\n")

    if not candidates:
        print("  Nothing to remove.")
        return 0

    # Show 10 examples
    for p in candidates[:10]:
        print(f"    {p.relative_to(target)}")
    if len(candidates) > 10:
        print(f"    ... and {len(candidates) - 10} more")
    print()

    if not _yes_or_ask("  Remove all stamped files?", yes=yes):
        print("  Cancelled.")
        return 0

    removed = 0
    for p in candidates:
        try:
            p.unlink()
            removed += 1
        except OSError as exc:
            print(f"  ⚠ couldn't remove {p}: {exc}")

    # Prune empty agent_os/ subdirs (best-effort, leaves user dirs alone).
    for root in (target_agent_os, target_vault):
        if not root.exists():
            continue
        for p in sorted(root.rglob("*"), key=lambda x: -len(x.parts)):
            if p.is_dir():
                try:
                    p.rmdir()
                except OSError:
                    pass

    print(f"\n✓ removed {removed} file(s).")
    return 0


# ---------------------------------------------------------------------------
# Kaioken mode (local fabric)
# ---------------------------------------------------------------------------

def _kaioken(*, yes: bool, telegram: bool) -> int:
    print("\n⚡ Hermes kaioken-mode install — local Docker fabric.\n")

    # Doctor: docker available
    docker_path = shutil.which("docker")
    if not docker_path:
        print("✗ docker not found on PATH.")
        print("  Install Docker Desktop: https://docs.docker.com/desktop/")
        return 2
    rc = subprocess.call(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rc != 0:
        print("✗ docker daemon not running. Start Docker Desktop and re-run.")
        return 2

    setup = SCRIPT_DIR / "scripts" / "setup.sh"
    up = SCRIPT_DIR / "scripts" / "kaioken-up.sh"
    if not up.exists():
        print(f"✗ {up} missing. Re-clone the repo.")
        return 2

    # Optional .env scaffolding via setup.sh in kaioken mode (it knows to
    # only ask for ANTHROPIC_API_KEY + optional TELEGRAM_BOT_TOKEN).
    if setup.exists() and _yes_or_ask("  Run scripts/setup.sh to scaffold .env?", yes=yes):
        env = os.environ.copy()
        env["HERMES_INSTALL_MODE"] = "kaioken"
        rc = subprocess.call(["bash", str(setup)], env=env)
        if rc != 0:
            print("✗ setup.sh exited non-zero — re-run when ready.")
            return rc

    print("\n==> Bringing up the fabric")
    cmd = ["bash", str(up)]
    if telegram:
        cmd.append("--telegram")
    rc = subprocess.call(cmd)
    if rc != 0:
        return rc

    print("\n✓ kaioken install complete.")
    print("  Demo:        uv run python examples/kaioken_spawn_demo.py")
    print("  Tear down:   ./scripts/kaioken-down.sh")
    return 0


# ---------------------------------------------------------------------------
# Super-saiyan-5 mode (cloud)
# ---------------------------------------------------------------------------

def _super_saiyan_5() -> int:
    setup = SCRIPT_DIR / "scripts" / "setup.sh"
    deploy = SCRIPT_DIR / "scripts" / "deploy.sh"
    if not setup.exists() or not deploy.exists():
        print("✗ scripts/setup.sh or scripts/deploy.sh missing. Are you running "
              "install.py from the hermes-super-agent repo root?")
        return 2

    print("\n🔵 Hermes super-saiyan-5-mode install — full Railway + DO fabric.\n")
    print("  This runs:  scripts/setup.sh   (interactive credentials)")
    print("              scripts/deploy.sh  (Railway deploy of 5 services)\n")

    env = os.environ.copy()
    env["HERMES_INSTALL_MODE"] = "super-saiyan-5"

    rc = subprocess.call(["bash", str(setup)], env=env)
    if rc != 0:
        return rc
    return subprocess.call(["bash", str(deploy)], env=env)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _yes_or_ask(prompt: str, *, yes: bool) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        # Non-interactive without --yes → default to NO (safe).
        return False
    try:
        ans = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return ans in ("y", "yes")


def _repo_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=SCRIPT_DIR, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())
