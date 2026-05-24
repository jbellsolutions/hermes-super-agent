#!/usr/bin/env python3
"""Saiyan-mode hello agent — proves the installed orchestrator actually runs.

This is the "did the install work?" example. It uses ONLY the `terminal`
runtime, which has no API-key dependencies — just shells out to a local
command — so it works in any fresh project right after `install.py --mode=saiyan`.

Usage:
    python examples/saiyan_hello.py --prompt "echo hello"
    python examples/saiyan_hello.py --prompt "ls -la" --quiet

Exit codes:
    0  ran successfully, runtime returned non-empty output
    1  install incomplete (import failed, runtime errored, no output)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import asdict, is_dataclass


async def _run(prompt: str, quiet: bool) -> int:
    try:
        from agent_os.orchestrator.adapters.job_router import Job, dispatch
        from agent_os.orchestrator.tool_planner import plan
        from agent_os.orchestrator.plan_card import render
    except ImportError as exc:
        print(f"✗ import failed: {exc}", file=sys.stderr)
        print("  Did you run `pip install -r requirements.txt` (or `uv sync`)?",
              file=sys.stderr)
        return 1

    # Force the `terminal` runtime by tagging the job + supplying the command
    # in metadata. No LLM, no API keys, just runs the prompt as a shell command.
    job = Job(
        prompt=prompt,
        tags={"script"},
        metadata={"shell_command": prompt},
    )
    try:
        tool_plan = plan(job)
    except Exception as exc:
        print(f"✗ planner failed: {exc}", file=sys.stderr)
        return 1

    if not quiet:
        try:
            print(render(tool_plan))
            print()
        except Exception:
            # plan_card.render can fail if catalog.yaml is missing in a fresh
            # install. Don't let it block the actual dispatch.
            pass

    try:
        result = await dispatch(job, plan=tool_plan)
    except Exception as exc:
        print(f"✗ dispatch failed: {exc}", file=sys.stderr)
        return 1

    # dispatch() returns a RuntimeResult dataclass for sync runtimes.
    # Normalize to a dict so we can read fields uniformly.
    if is_dataclass(result):
        data = asdict(result)
    elif isinstance(result, dict):
        data = result
    else:
        print(f"✗ runtime returned unexpected shape: {type(result).__name__}",
              file=sys.stderr)
        return 1

    status = data.get("status", "unknown")
    output = data.get("output")
    error = data.get("error")

    # Flatten nested output dict if the runtime returned one (terminal does
    # for non-zero exits).
    if isinstance(output, dict):
        output_str = output.get("stdout") or output.get("note") or str(output)
    else:
        output_str = str(output) if output is not None else ""

    if not quiet:
        print(f"  status:  {status}")
        if error:
            print(f"  error:   {error}")
        print(f"  output:  {output_str.strip()}")

    if status not in ("completed", "ok", "success"):
        print(f"✗ runtime status: {status}", file=sys.stderr)
        if error:
            print(f"  error: {error}", file=sys.stderr)
        return 1
    if not output_str.strip():
        print("✗ runtime returned empty output", file=sys.stderr)
        return 1

    # Stream the trimmed output to stdout so install.py can grep it.
    print(output_str.strip())
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--prompt", default="echo hello",
                   help="Shell command to run (default: 'echo hello').")
    p.add_argument("--quiet", action="store_true",
                   help="Skip plan card and metadata — only print output.")
    args = p.parse_args()
    return asyncio.run(_run(args.prompt, args.quiet))


if __name__ == "__main__":
    sys.exit(main())
