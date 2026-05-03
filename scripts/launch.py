#!/usr/bin/env python3
"""agent-os conversational launch wizard.

Two modes:
    ./scripts/launch.py              full prompt walkthrough
    ./scripts/launch.py --minimal    only the absolute minimum (Path C: let Hermes finish)

The wizard runs a Step 0 Hermes Agent preflight. If the `hermes` CLI is missing,
it installs Hermes from the official Nous Research installer before continuing.

Idempotent — re-run any time to change settings. Reads existing .env and only
re-prompts for missing/blank values unless --reset is passed.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
HERMES_INSTALL_COMMAND = (
    "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh"
    " | bash"
)


def color(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def green(s: str) -> str:
    return color(s, "32")


def cyan(s: str) -> str:
    return color(s, "36")


def yellow(s: str) -> str:
    return color(s, "33")


def red(s: str) -> str:
    return color(s, "31")


def banner() -> None:
    print()
    print(cyan("Super Agent — launch wizard"))
    print(cyan("─" * 40))
    print("Commercial-grade agent setup. One operator, many specialist agents when needed.")
    print()


def prompt(question: str, default: str = "", required: bool = False, secret: bool = False) -> str:
    """Ask a single question. Re-prompts if required + empty."""
    suffix = f" [{default}]" if default else ""
    if secret:
        suffix += " (input hidden)"
    while True:
        try:
            if secret:
                import getpass

                ans = getpass.getpass(f"{question}{suffix}: ").strip()
            else:
                ans = input(f"{question}{suffix}: ").strip()
        except EOFError:
            ans = ""
        ans = ans or default
        if ans or not required:
            return ans
        print(red("  required — try again"))


def prompt_yn(question: str, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    ans = input(f"{question} [{d}]: ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")


def prompt_choice(question: str, options: list[str], default_idx: int = 0) -> str:
    print(question)
    for i, o in enumerate(options):
        marker = "*" if i == default_idx else " "
        print(f"  {marker} [{i + 1}] {o}")
    raw = input(f"  pick a number [{default_idx + 1}]: ").strip()
    if not raw:
        return options[default_idx]
    try:
        return options[int(raw) - 1]
    except (ValueError, IndexError):
        print(red("  invalid choice; using default"))
        return options[default_idx]


def _run_hermes_version() -> subprocess.CompletedProcess[str]:
    """Return `hermes --version`, using a login-ish shell if PATH was just updated."""
    if shutil.which("hermes"):
        return subprocess.run(["hermes", "--version"], cwd=ROOT, text=True, capture_output=True)
    return subprocess.run(
        ["bash", "-lc", "hermes --version"], cwd=ROOT, text=True, capture_output=True
    )


def step_hermes_preflight(skip_install: bool) -> bool:
    print()
    print(cyan("Step 0 — Hermes Agent preflight"))
    print()

    version = _run_hermes_version()
    if version.returncode == 0:
        print(green(f"  Hermes installed: {version.stdout.strip()}"))
        return True

    if skip_install:
        print(yellow("  --skip-hermes-install passed; not installing Hermes Agent"))
        print(yellow("  Install manually, then re-run: hermes doctor && hermes"))
        return True

    print(yellow("  Hermes Agent is missing. Installing Hermes first, then continuing the wizard."))
    print(f"  running: {HERMES_INSTALL_COMMAND}")
    install = subprocess.run(["bash", "-lc", HERMES_INSTALL_COMMAND], cwd=ROOT)
    if install.returncode != 0:
        print(red("  Hermes install failed — install manually, then re-run this wizard"))
        print(f"  {HERMES_INSTALL_COMMAND}")
        return False

    version = _run_hermes_version()
    if version.returncode != 0:
        print(yellow("  Hermes installer finished, but this terminal cannot find `hermes` yet."))
        print(yellow("  Open a new terminal or source your shell profile, then run:"))
        print("    hermes doctor")
        print("    ./scripts/launch.py")
        return False

    print(green(f"  Hermes installed: {version.stdout.strip()}"))
    print(
        "  Run `hermes setup` after this wizard if your Hermes model/provider is not "
        "configured yet."
    )
    return True


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        if ENV_EXAMPLE.exists():
            shutil.copy(ENV_EXAMPLE, ENV_FILE)
            print(green("  created .env from .env.example"))
    out: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def write_env(env: dict[str, str]) -> None:
    """Preserve comments + ordering from .env.example, fill in values."""
    template = ENV_EXAMPLE.read_text() if ENV_EXAMPLE.exists() else ""
    new_lines: list[str] = []
    seen: set[str] = set()
    for line in template.splitlines():
        s = line.strip()
        if "=" in s and not s.startswith("#"):
            k = s.split("=", 1)[0].strip()
            if k in env:
                new_lines.append(f"{k}={env[k]}")
                seen.add(k)
                continue
        new_lines.append(line)
    # Append any keys we set that weren't in the template
    for k, v in env.items():
        if k not in seen:
            new_lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n")
    print(green(f"  wrote {ENV_FILE.relative_to(ROOT)}"))


def step_keys(env: dict[str, str], minimal: bool, reset: bool) -> dict[str, str]:
    print()
    print(cyan("Step 1 — channels and keys"))
    print()

    operator = env.get("AGENT_OS_OWNER") if not reset else ""
    if not operator:
        operator = prompt(
            "Operator name (the canonical identity for cross-channel memory)",
            default="justin",
            required=True,
        )
        env["AGENT_OS_OWNER"] = operator

    if not env.get("ANTHROPIC_API_KEY") or reset:
        env["ANTHROPIC_API_KEY"] = prompt(
            "ANTHROPIC_API_KEY (Claude Opus 4.6/4.7 for content/design + architecture review)",
            default=env.get("ANTHROPIC_API_KEY", ""),
            required=True,
            secret=True,
        )

    if not env.get("OPENAI_API_KEY") or reset:
        if prompt_yn(
            "Configure OPENAI_API_KEY now? "
            "(GPT-5.5/Codex recommended for dual-frontier architecture + coding)",
            default=True,
        ):
            env["OPENAI_API_KEY"] = prompt(
                "OPENAI_API_KEY",
                default=env.get("OPENAI_API_KEY", ""),
                secret=True,
            )

    if not env.get("HERMES_DEFAULT_MODEL") or reset:
        env["HERMES_DEFAULT_MODEL"] = prompt(
            "Default model for Hermes",
            default=env.get("HERMES_DEFAULT_MODEL", "claude-opus-4-7"),
        )
    if not env.get("HERMES_ARCHITECTURE_MODELS") or reset:
        env["HERMES_ARCHITECTURE_MODELS"] = prompt(
            "Architecture/debug/security/auth/tests model team",
            default=env.get("HERMES_ARCHITECTURE_MODELS", "gpt-5.5,claude-opus-4-7"),
        )
    if not env.get("HERMES_WORKER_MODEL") or reset:
        env["HERMES_WORKER_MODEL"] = prompt(
            "Lower-cost worker model",
            default=env.get("HERMES_WORKER_MODEL", "deepseek"),
        )

    if not env.get("SUPER_AGENT_TIER") or reset:
        tier = prompt_choice(
            "Commercial setup tier:",
            ["operator", "pro-operator", "enterprise"],
            default_idx=0,
        )
        env["SUPER_AGENT_TIER"] = tier

    print()
    print(cyan("Business onboarding"))
    if not env.get("BUSINESS_NAME") or reset:
        env["BUSINESS_NAME"] = prompt(
            "Business/project name this agent is being set up for",
            default=env.get("BUSINESS_NAME", "internal-super-agent"),
        )
    if not env.get("BUSINESS_TYPE") or reset:
        env["BUSINESS_TYPE"] = prompt(
            "Business type / offer (example: COO dashboard, SDR agency, paperclip business)",
            default=env.get("BUSINESS_TYPE", "operator command center"),
        )
    if not env.get("FIRST_WORKFLOWS") or reset:
        env["FIRST_WORKFLOWS"] = prompt(
            "First 3 workflows the agent should own (comma-separated)",
            default=env.get("FIRST_WORKFLOWS", "daily status, deployment inventory, repo updates"),
        )
    if not env.get("HUMAN_APPROVAL_REQUIRED") or reset:
        env["HUMAN_APPROVAL_REQUIRED"] = prompt(
            "Actions requiring human approval",
            default=env.get(
                "HUMAN_APPROVAL_REQUIRED",
                "production deploys, payments, destructive infra changes, outbound sending",
            ),
        )

    print()
    print(cyan("Shared brain sync"))
    print(
        "Obsidian + Notion are the shared read/write brain. Configure what you have now; "
        "mark Notion pending if needed."
    )
    if not env.get("OBSIDIAN_VAULT_PATH") or reset:
        env["OBSIDIAN_VAULT_PATH"] = prompt(
            "Obsidian vault path",
            default=env.get("OBSIDIAN_VAULT_PATH", "~/Documents/Obsidian Vault"),
        )
    if not env.get("SHARED_BRAIN_SYNC_MODE") or reset:
        env["SHARED_BRAIN_SYNC_MODE"] = "bidirectional"
    if not env.get("NOTION_API_KEY") or reset:
        if prompt_yn("  Configure Notion API key/database IDs now?", default=False):
            env["NOTION_API_KEY"] = prompt("  NOTION_API_KEY", secret=True)
            for k in (
                "NOTION_CONVERSATIONS_DB",
                "NOTION_ACTIONS_DB",
                "NOTION_DECISIONS_DB",
                "NOTION_AGENTS_DB",
                "NOTION_COMPANIES_DB",
                "NOTION_DEPLOYMENTS_DB",
                "NOTION_APPROVALS_DB",
                "NOTION_COSTS_DB",
            ):
                if not env.get(k) or reset:
                    env[k] = prompt(f"  {k}", default=env.get(k, ""))

    if minimal:
        return env

    channels: list[str] = []
    print()
    print("Which channels do you want active first?")
    if prompt_yn("  Slack", default=True):
        channels.append("slack")
    if prompt_yn("  Telegram", default=False):
        channels.append("telegram")
    if prompt_yn("  Web text chat (no extra keys)", default=True):
        channels.append("web")
    if prompt_yn("  Web voice (LiveKit + OpenAI/Gemini Realtime)", default=False):
        channels.append("voice")

    if "slack" in channels:
        print()
        print(yellow("  Slack — create at https://api.slack.com/apps if you haven't"))
        for k in ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET"):
            if not env.get(k) or reset:
                env[k] = prompt(f"  {k}", secret=True)

    if "telegram" in channels:
        print()
        print(yellow("  Telegram — talk to @BotFather"))
        if not env.get("TELEGRAM_BOT_TOKEN") or reset:
            env["TELEGRAM_BOT_TOKEN"] = prompt("  TELEGRAM_BOT_TOKEN", secret=True)

    if "voice" in channels:
        print()
        print(yellow("  Voice — LiveKit (self-host or LiveKit Cloud free tier)"))
        for k in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
            if not env.get(k) or reset:
                env[k] = prompt(f"  {k}", secret=k.endswith("SECRET"))
        provider = prompt_choice(
            "  Voice realtime provider:",
            ["openai", "gemini"],
            default_idx=0,
        )
        env["VOICE_REALTIME_PROVIDER"] = provider
        if provider == "openai" and (not env.get("OPENAI_API_KEY") or reset):
            env["OPENAI_API_KEY"] = prompt("  OPENAI_API_KEY", secret=True)
        if provider == "gemini" and (not env.get("GEMINI_API_KEY") or reset):
            env["GEMINI_API_KEY"] = prompt("  GEMINI_API_KEY", secret=True)

    print()
    print(cyan("Composio (built-in tool access)"))
    print("(one key unlocks 250+ SaaS connectors — Slack, Gmail, Linear, Notion,")
    print(" HubSpot, etc. Hermes discovers + invokes them on demand. Free tier covers most usage.)")
    if not env.get("COMPOSIO_API_KEY") or reset:
        if prompt_yn("  Configure COMPOSIO_API_KEY now? (recommended)", default=True):
            env["COMPOSIO_API_KEY"] = prompt("    COMPOSIO_API_KEY", secret=True)

    print()
    print(cyan("Optional specialist-runtime keys"))
    print("(skip any — the runtime stays disabled if its key is blank)")
    optional = [
        ("OPENAI_API_KEY", "Codex CLI runtime / GPT-5.5 dual-frontier reviewer"),
        ("CURSOR_API_KEY", "Cursor SDK builder-swarm backend"),
        ("E2B_API_KEY", "E2B sandboxed code execution (free tier at e2b.dev)"),
        ("EXA_API_KEY", "Exa neural search (free tier at exa.ai)"),
        ("OPENROUTER_API_KEY", "OpenRouter for non-Anthropic / non-OpenAI models"),
        ("RAILWAY_TOKEN", "Railway deployment discovery/deploys"),
        ("DIGITALOCEAN_ACCESS_TOKEN", "DigitalOcean droplet/app discovery"),
    ]
    for k, desc in optional:
        if env.get(k) and not reset:
            continue
        if prompt_yn(f"  Configure {k} ({desc})?", default=False):
            env[k] = prompt(f"    {k}", secret=True)

    if env.get("SUPER_AGENT_TIER") == "enterprise":
        print()
        print(cyan("Enterprise-only managed cloud computer"))
        print(
            "Orgo AI or similar is optional. Skip unless this customer/workspace needs an "
            "isolated visible desktop."
        )
        if prompt_yn("  Enable optional Orgo/managed-cloud-computer placeholder?", default=False):
            env["ORGO_ENABLED"] = "true"
            if not env.get("ORGO_API_KEY") or reset:
                env["ORGO_API_KEY"] = prompt("    ORGO_API_KEY", secret=True)
        else:
            env["ORGO_ENABLED"] = "false"

    return env


def step_deploy() -> str:
    print()
    print(cyan("Step 2 — deploy target"))
    print()
    return prompt_choice(
        "Where will agent-os run?",
        ["local-only (just for now)", "railway", "docker-compose", "fly"],
        default_idx=0,
    )


def step_bootstrap(skip_install: bool) -> bool:
    print()
    print(cyan("Step 3 — bootstrap"))
    print()
    if skip_install:
        print(yellow("  --skip-install passed; not running uv sync / pnpm install"))
        return True

    bootstrap = ROOT / "scripts" / "bootstrap.sh"
    if not bootstrap.exists():
        print(red(f"  missing {bootstrap}"))
        return False
    print("  running ./scripts/bootstrap.sh ...")
    r = subprocess.run([str(bootstrap)], cwd=ROOT)
    if r.returncode != 0:
        print(red("  bootstrap failed — fix and re-run"))
        return False
    print(green("  bootstrap OK"))
    return True


def step_smoke() -> bool:
    print()
    print(cyan("Step 4 — smoke tests"))
    print()
    r = subprocess.run(["uv", "run", "pytest", "-q"], cwd=ROOT)
    if r.returncode != 0:
        print(red("  smoke FAILED — fix before continuing"))
        return False
    print(green("  smoke OK"))
    return True


def step_manifest() -> bool:
    print()
    print(cyan("Step 5 — build system graph"))
    print()
    r = subprocess.run(["uv", "run", "python", "-m", "agent_os.manifest.aggregator"], cwd=ROOT)
    if r.returncode != 0:
        print(red("  manifest aggregator failed"))
        return False
    print(green("  graph written to vault/graph/system.yaml"))
    return True


def step_summary(env: dict[str, str], deploy: str) -> None:
    print()
    print(cyan("─" * 40))
    print(green("Super Agent scaffold is ready. Hermes launches through the Hermes CLI."))
    print(cyan("─" * 40))
    print()
    print(f"  operator:        {env.get('AGENT_OS_OWNER', '?')}")
    print(f"  tier:            {env.get('SUPER_AGENT_TIER', 'operator')}")
    print(f"  business:        {env.get('BUSINESS_NAME', '?')} — {env.get('BUSINESS_TYPE', '?')}")
    print(f"  workflows:       {env.get('FIRST_WORKFLOWS', '?')}")
    print(f"  default model:   {env.get('HERMES_DEFAULT_MODEL', '?')}")
    print(f"  deploy target:   {deploy}")
    channels_on = []
    if env.get("SLACK_BOT_TOKEN"):
        channels_on.append("slack")
    if env.get("TELEGRAM_BOT_TOKEN"):
        channels_on.append("telegram")
    channels_on.append("web (always)")
    if env.get("LIVEKIT_API_KEY"):
        channels_on.append("voice")
    print(f"  channels:        {', '.join(channels_on)}")
    if env.get("COMPOSIO_API_KEY"):
        print("  composio:        enabled (250+ tools available to Hermes on demand)")
    else:
        print("  composio:        disabled (re-run with --reset to add COMPOSIO_API_KEY)")
    print()
    print("Daily loops (run automatically once Hermes is booted):")
    print("  02:00  upgrader pulls Hermes/OpenClaw/browser-use/Aider/Codex/agi-1/community skills")
    print("  02:30  /agi-audit scores the day's outputs")
    print("  every 5 min — heartbeat self-healing loop")
    print()
    print("Next moves:")
    print(f"  {green('hermes doctor')}          — verify the real Hermes install")
    print(f"  {green('hermes')}                 — start the real Hermes CLI chat")
    print(f"  {green('hermes gateway setup')}   — optional: configure Telegram/Slack")
    print(
        f"  {green('uv run agent-os boot')}   — diagnostic only; Stage 2 scaffold, "
        "not the live Hermes launcher yet"
    )
    print(f"  {green('uv run agent-os manifest')} — refresh the Super Agent system graph")
    print(f"  {green('uv run agent-os explain')}  — query the graph in plain English")
    print()
    print(
        "Read docs/commercial-packaging.md for tier rules and "
        "docs/portfolio-agent-architecture.md for specialist-agent expansion."
    )
    print("Stage 2+ of docs/EXECUTION-PLAN.md is where the stubbed runtimes get real wiring.")
    print()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--minimal", action="store_true", help="only ANTHROPIC_API_KEY + operator")
    p.add_argument(
        "--reset",
        action="store_true",
        help="re-prompt for all values, ignoring existing .env",
    )
    p.add_argument("--skip-install", action="store_true", help="skip uv sync / pnpm install")
    p.add_argument(
        "--skip-hermes-install",
        action="store_true",
        help="do not auto-install Hermes Agent if the hermes CLI is missing",
    )
    args = p.parse_args()

    banner()
    if not step_hermes_preflight(skip_install=args.skip_hermes_install):
        return 1
    env = load_env()
    env = step_keys(env, minimal=args.minimal, reset=args.reset)
    write_env(env)
    deploy = step_deploy() if not args.minimal else "local-only (just for now)"

    ok = step_bootstrap(skip_install=args.skip_install)
    if not ok:
        return 1
    ok = step_smoke()
    if not ok:
        return 1
    ok = step_manifest()
    if not ok:
        return 1
    step_summary(env, deploy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
