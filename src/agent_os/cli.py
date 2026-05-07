"""agent-os CLI entry point. `agent-os` after `uv sync` runs this."""
from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-os", description="agent-os control surface")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("boot", help="Show Hermes boot status/guidance (Stage 2 scaffold; use `hermes` to start live CLI)")
    sub.add_parser("upgrade", help="Run nightly upgrader (all 11 streams)")
    sub.add_parser("manifest", help="Rebuild the system graph from manifest.yaml files")
    p_explain = sub.add_parser("explain", help="Walk the system graph in plain language")
    p_explain.add_argument("query", nargs="?", default="whats-running")

    p_route = sub.add_parser("route", help="Show which runtime would handle a job")
    p_route.add_argument("--tags", nargs="*", default=[])
    p_route.add_argument("--prompt", default="")

    p_plan = sub.add_parser(
        "plan", help="Show the tool plan card for a job (tool + model + tier)"
    )
    p_plan.add_argument("--tags", nargs="*", default=[])
    p_plan.add_argument("--prompt", default="")
    p_plan.add_argument("--identity", default="primary_hermes")
    p_plan.add_argument(
        "--format", choices=["markdown", "json", "why"], default="markdown",
    )

    p_tier = sub.add_parser("tier", help="Classify a job's tier (1/2/3) without invoking")
    p_tier.add_argument("--tags", nargs="*", default=[])
    p_tier.add_argument("--prompt", default="")
    p_tier.add_argument("--cost-usd", type=float, default=None)
    p_tier.add_argument("--minutes", type=float, default=None)

    sub.add_parser("catalog", help="Rebuild vault/graph/tool-catalog.yaml + cheatsheets")
    p_tool = sub.add_parser("tool", help="Show one tool's SKILL.md")
    p_tool.add_argument("name")

    sub.add_parser("models", help="List registered models from config/models.yaml")

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
    elif args.cmd == "plan":
        from agent_os.orchestrator import plan_card
        from agent_os.orchestrator.adapters.job_router import Job
        from agent_os.orchestrator.tool_planner import plan as plan_fn

        job = Job(prompt=args.prompt, tags=set(args.tags))
        result = plan_fn(job, identity=args.identity)
        print(plan_card.render(result, channel=args.format))
    elif args.cmd == "tier":
        from agent_os.orchestrator import tier_classifier
        from agent_os.orchestrator.adapters.job_router import Job

        job = Job(prompt=args.prompt, tags=set(args.tags))
        decision = tier_classifier.classify(
            job, cost_usd=args.cost_usd, estimated_minutes=args.minutes,
        )
        print(json.dumps({
            "tier": decision.tier,
            "reason": decision.reason,
            "matched_rule": decision.matched_rule,
            "signals": decision.signals,
        }, indent=2))
    elif args.cmd == "catalog":
        from agent_os.orchestrator.catalog import regenerate_all
        print(json.dumps(regenerate_all(), indent=2))
    elif args.cmd == "tool":
        from agent_os.orchestrator.catalog import show_tool
        print(show_tool(args.name))
    elif args.cmd == "models":
        from agent_os.orchestrator.catalog import list_models
        models = list_models()
        if not models:
            print("(no models registered — check src/agent_os/orchestrator/config/models.yaml)")
        else:
            for name in sorted(models):
                m = models[name]
                cost_in = m.get("cost_per_mtok_in", "?")
                cost_out = m.get("cost_per_mtok_out", "?")
                tcs = ", ".join((m.get("task_classes") or [])[:4])
                print(f"  {name:24s}  ${cost_in}/${cost_out}  [{tcs}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
