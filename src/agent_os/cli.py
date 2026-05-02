"""agent-os CLI entry point. `agent-os` after `uv sync` runs this."""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-os", description="agent-os control surface")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("boot", help="Boot Hermes orchestrator")
    sub.add_parser("upgrade", help="Run nightly upgrader (all 10 streams)")
    sub.add_parser("manifest", help="Rebuild the system graph from manifest.yaml files")
    p_explain = sub.add_parser("explain", help="Walk the system graph in plain language")
    p_explain.add_argument("query", nargs="?", default="whats-running")
    p_route = sub.add_parser("route", help="Show which runtime would handle a job")
    p_route.add_argument("--tags", nargs="*", default=[])
    p_route.add_argument("--prompt", default="")

    args = parser.parse_args(argv)

    if args.cmd == "boot":
        from agent_os.orchestrator.boot import boot_hermes
        print(json.dumps(boot_hermes(), indent=2))
    elif args.cmd == "upgrade":
        from agent_os.upgrader.daemon import run_nightly
        print(json.dumps(run_nightly(), indent=2))
    elif args.cmd == "manifest":
        from agent_os.manifest.aggregator import build_graph
        g = build_graph()
        print(json.dumps({"nodes": len(g["nodes"]), "edges": len(g["edges"])}, indent=2))
    elif args.cmd == "explain":
        from agent_os.manifest.explain import changed_in_last_24h, what_depends_on, whats_running
        if args.query == "whats-running":
            print(whats_running())
        elif args.query == "changed":
            print(changed_in_last_24h())
        else:
            print(json.dumps({"depends_on": what_depends_on(args.query)}, indent=2))
    elif args.cmd == "route":
        from agent_os.orchestrator.adapters.job_router import Job, route
        runtime = route(Job(prompt=args.prompt, tags=set(args.tags)))
        print(runtime)
    return 0


if __name__ == "__main__":
    sys.exit(main())
