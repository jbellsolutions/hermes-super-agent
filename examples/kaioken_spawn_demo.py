#!/usr/bin/env python3
"""Kaioken spawn demo — prove the full local fabric actually fans out.

What this script does:
  1. Submits a Tier 2 job tagged `spawn-superagent` to the local Admiral
     (via the in-process orchestrator — no need to round-trip through A2A
     for the demo).
  2. The router (HERMES_MODE=kaioken) selects the `local_spawn` runtime.
  3. local_spawner.py uses the Docker SDK to spawn N sibling containers
     on the `hermes-fabric` network, each running the same Admiral image
     with HERMES_ROLE=worker and a different identity.
  4. Waits for each child's /agentCard to respond 200.
  5. Prints the results and tears the containers down (unless --keep).

Run AFTER `./scripts/kaioken-up.sh` has brought the fabric up.

Usage:
    python examples/kaioken_spawn_demo.py                  # spawn 3, tear down
    python examples/kaioken_spawn_demo.py --count 5        # spawn 5
    python examples/kaioken_spawn_demo.py --keep           # leave them running

Exit codes:
    0  all spawns completed and (if not --keep) cleaned up
    1  any spawn failed; surviving containers left for you to inspect
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time


_DEFAULT_MARKETS = [
    "small-business legal services",
    "boutique fitness studios",
    "specialty coffee roasters",
]


async def _spawn_one(prompt: str, identity: str) -> dict:
    from agent_os.orchestrator.adapters.job_router import Job, dispatch

    job = Job(
        prompt=prompt,
        tags={"spawn-superagent"},
        metadata={
            "identity": identity,
            "parent_a2a": "http://hermes-admiral:8080",
        },
    )
    # Spawn jobs are tag-driven — don't pass a tool_plan. Even if we did,
    # the dispatch fabric-route override would ignore plan.primary_tool for
    # spawn intents; explicit beats accidental.
    return await dispatch(job)


async def _teardown(container_names: list[str]) -> None:
    """Stop + remove the spawned containers. Best-effort."""
    try:
        import docker  # type: ignore[import-untyped]
        client = docker.from_env()
    except Exception as exc:
        print(f"  (skip teardown — docker SDK unavailable: {exc})")
        return
    for name in container_names:
        try:
            c = client.containers.get(name)
            c.stop(timeout=5)
            c.remove()
            print(f"  removed {name}")
        except Exception as exc:
            print(f"  ⚠ could not remove {name}: {exc}")


async def _main(count: int, keep: bool, markets: list[str]) -> int:
    os.environ.setdefault("HERMES_MODE", "kaioken")

    print(f"⚡ Kaioken demo — spawning {count} local superagent(s)\n")

    t0 = time.monotonic()
    tasks = [
        _spawn_one(
            prompt=f"Research the {markets[i % len(markets)]} market and write me a one-page brief.",
            identity=f"researcher-{i+1}",
        )
        for i in range(count)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    container_names = []
    failed = 0
    for i, r in enumerate(results, 1):
        if isinstance(r, BaseException):
            print(f"  ✗ spawn {i}: {type(r).__name__}: {r}")
            failed += 1
            continue
        if not isinstance(r, dict):
            print(f"  ✗ spawn {i}: unexpected result type {type(r).__name__}")
            failed += 1
            continue
        if r.get("status") != "completed":
            print(f"  ✗ spawn {i}: status={r.get('status')} error={r.get('error', '')}")
            failed += 1
            continue
        name = r.get("container_name", "?")
        container_names.append(name)
        elapsed = r.get("elapsed_seconds", 0)
        a2a = r.get("a2a_endpoint", "?")
        host = r.get("host_endpoint")
        suffix = f"  (host: {host})" if host else ""
        print(f"  ✓ spawn {i}: {name}  ({elapsed:.1f}s)  → {a2a}{suffix}")

    total = time.monotonic() - t0
    print(f"\n  total: {len(container_names)}/{count} healthy in {total:.1f}s")

    if container_names and not keep:
        print("\n==> Tearing down spawned containers")
        await _teardown(container_names)
    elif keep and container_names:
        print(f"\n  --keep: {len(container_names)} containers left running")
        print("  Stop them with: ./scripts/kaioken-down.sh --kill-spawns")

    return 0 if failed == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    p.add_argument("--count", type=int, default=3,
                   help="Number of superagents to spawn in parallel (default: 3).")
    p.add_argument("--keep", action="store_true",
                   help="Leave the spawned containers running after the demo.")
    p.add_argument("--markets", nargs="*", default=_DEFAULT_MARKETS,
                   help="Space-separated list of market names to assign to spawns.")
    args = p.parse_args()
    return asyncio.run(_main(args.count, args.keep, args.markets))


if __name__ == "__main__":
    sys.exit(main())
