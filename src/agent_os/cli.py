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

    p_run = sub.add_parser(
        "run",
        help="End-to-end: tier-classify → plan → dispatch (the Admiral pipeline)",
    )
    p_run.add_argument("--prompt", required=True)
    p_run.add_argument("--tags", nargs="*", default=[])
    p_run.add_argument("--identity", default="primary_hermes")
    p_run.add_argument("--minutes", type=float, default=None)
    p_run.add_argument("--cost-usd", type=float, default=None)
    p_run.add_argument(
        "--yes",
        action="store_true",
        help="Skip the Tier 2/3 confirmation gate (autonomous mode).",
    )
    p_run.add_argument("--meta", action="append", default=[], metavar="KEY=VALUE")

    sub.add_parser(
        "doctor",
        help="Check your local config — env vars, reachability of Coordinator/NATS/etc.",
    )

    p_spawn = sub.add_parser(
        "spawn",
        help="Spawn a Tier 1 specialist (Railway) or Tier 2 superagent (VPS).",
    )
    p_spawn.add_argument("--tier", type=int, choices=[1, 2], required=True)
    p_spawn.add_argument("--prompt", required=True, help="Spec for what to build/spawn.")
    p_spawn.add_argument("--name", default="", help="Optional explicit agent_id; otherwise slugged from prompt.")
    p_spawn.add_argument("--meta", action="append", default=[], metavar="KEY=VALUE")

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
    elif args.cmd == "run":
        return _cmd_run(args)
    elif args.cmd == "spawn":
        return _cmd_spawn(args)
    elif args.cmd == "doctor":
        return _cmd_doctor()
    return 0


def _cmd_doctor() -> int:
    """Diagnose local config. Returns 0 if all critical checks pass."""
    import os

    G = "\033[32m"; Y = "\033[33m"; R_ = "\033[31m"; D = "\033[2m"; END = "\033[0m"
    ok = G + "✓" + END
    warn = Y + "!" + END
    bad = R_ + "✗" + END

    failures = 0
    print()
    print("Hermes doctor — local config check")
    print()

    def check(label, condition, hint="", critical=True):
        nonlocal failures
        if condition:
            print(f"  {ok} {label}")
        else:
            print(f"  {bad if critical else warn} {label}  {D}— {hint}{END}")
            if critical:
                failures += 1

    # Env presence
    keys = {
        "ANTHROPIC_API_KEY": True,   # critical
        "TELEGRAM_BOT_TOKEN": True,
        "TELEGRAM_CHAT_ID": True,
        "OPENAI_API_KEY": False,
        "COORDINATOR_URL": False,
        "NATS_URL": False,
        "TEMPORAL_HOST": False,
        "DO_API_TOKEN": False,
        "RETELL_API_KEY": False,
        "INSTANTLY_API_KEY": False,
        "AGENTOPS_API_KEY": False,
    }
    for k, critical in keys.items():
        val = os.getenv(k, "")
        check(f"env {k}", bool(val), "set in .env", critical=critical)

    # Reachability checks (only if URLs configured)
    coord_url = os.getenv("COORDINATOR_URL", "")
    if coord_url:
        try:
            import httpx
            r = httpx.get(coord_url + "/health", timeout=5)
            check(f"Coordinator /health → {r.status_code}", r.status_code == 200,
                  f"Got {r.status_code}", critical=False)
        except Exception as exc:
            check("Coordinator reachable", False, str(exc)[:60], critical=False)

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if tg_token:
        try:
            import httpx
            r = httpx.get(f"https://api.telegram.org/bot{tg_token}/getMe", timeout=5)
            ok_tg = r.status_code == 200 and r.json().get("ok") is True
            name = r.json().get("result", {}).get("username", "?") if ok_tg else "?"
            check(f"Telegram bot @{name}", ok_tg, "bad token?", critical=False)
        except Exception as exc:
            check("Telegram API reachable", False, str(exc)[:60], critical=False)

    # Anthropic — verify the key actually authenticates without spending tokens
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            import httpx
            # GET /v1/models is a free endpoint that validates the key
            r = httpx.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01"},
                timeout=5,
            )
            check(f"Anthropic key valid (HTTP {r.status_code})", r.status_code == 200,
                  "key rejected" if r.status_code in (401, 403) else f"got {r.status_code}",
                  critical=False)
        except Exception as exc:
            check("Anthropic API reachable", False, str(exc)[:60], critical=False)

    # If TELEGRAM_BOT_TOKEN is set but TELEGRAM_CHAT_ID isn't, surface this loudly:
    # the bot will silently refuse messages, which is the correct behavior but
    # confusing without explanation.
    if tg_token and not os.getenv("TELEGRAM_CHAT_ID"):
        print(f"  {warn} TELEGRAM_BOT_TOKEN is set but TELEGRAM_CHAT_ID is empty —")
        print(f"    {D}the bot will refuse all messages until you set your chat ID.{END}")

    print()
    if failures == 0:
        print(f"  {ok} all critical checks passed")
        return 0
    print(f"  {bad} {failures} critical check(s) failed — run scripts/setup.sh to fix")
    return 1


def _parse_meta(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _cmd_run(args) -> int:
    """Full Admiral pipeline: tier_classifier → tool_planner → plan_card → dispatch."""
    import asyncio

    from agent_os.observability.agentops.client import init_agentops
    from agent_os.orchestrator import plan_card, tier_classifier
    from agent_os.orchestrator.adapters.job_router import Job, dispatch
    from agent_os.orchestrator.tool_planner import plan as plan_fn

    init_agentops(agent_id="admiral", tags=["cli-run"])

    job = Job(
        prompt=args.prompt,
        tags=set(args.tags),
        estimated_minutes=int(args.minutes) if args.minutes else None,
        metadata=_parse_meta(args.meta),
    )

    # 1. Tier classification
    decision = tier_classifier.classify(
        job, cost_usd=args.cost_usd, estimated_minutes=args.minutes,
    )

    # 2. Plan
    tool_plan = plan_fn(job, identity=args.identity)

    # 3. Plan card (always show)
    print(plan_card.render(tool_plan, channel="markdown"))
    print(f"\nTier: {decision.tier}  ({decision.matched_rule})")

    # 4. Approval gate for Tier 2/3
    if decision.tier >= 2 and not args.yes:
        print(f"\nTier {decision.tier} requires explicit confirmation. Re-run with --yes to dispatch.")
        return 0

    # 5. Dispatch
    print("\nDispatching...")
    try:
        result = asyncio.run(dispatch(job))
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    if hasattr(result, "__dict__"):
        from dataclasses import asdict, is_dataclass
        result_data = asdict(result) if is_dataclass(result) else vars(result)
    else:
        result_data = result
    print(json.dumps(result_data, indent=2, default=str))
    return 0 if (isinstance(result_data, dict) and result_data.get("status") != "error") else 1


def _cmd_spawn(args) -> int:
    """Spawn a Tier 1 specialist or Tier 2 superagent via spawner.spawn()."""
    import asyncio
    from agent_os.observability.agentops.client import init_agentops
    from agent_os.orchestrator.adapters.job_router import Job
    from agent_os.orchestrator.spawner import spawn

    init_agentops(agent_id="admiral", tags=["cli-spawn"])

    metadata = _parse_meta(args.meta)
    if args.name:
        metadata["agent_id"] = args.name

    tags = {"spawn-superagent"} if args.tier == 2 else {"build-specialist"}

    job = Job(prompt=args.prompt, tags=tags, metadata=metadata)
    result = asyncio.run(spawn(job))
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") not in ("error",) else 1


if __name__ == "__main__":
    sys.exit(main())
