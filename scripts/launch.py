#!/usr/bin/env python3
"""Super Agent conversational launch wizard.

The runnable twin of INSTALL.md's master prompt. Walks you through:

    1. Pick your power level — Saiyan or Super Saiyan
    2. Hermes preflight — install the Hermes runtime if it's missing
    3. Keys & channels — conversational, asks only for what your mode needs
    4. Install — mode-aware (saiyan drop-in, or Super Saiyan full bring-up)

Usage:
    ./scripts/launch.py                 full walkthrough, asks the mode
    ./scripts/launch.py --mode=saiyan   skip the mode question
    ./scripts/launch.py --minimal       absolute-minimum keys only

Idempotent — re-run any time. Reads existing .env and only re-prompts for
missing/blank values unless --reset is passed.
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

# Mode descriptions — kept word-for-word in sync with INSTALL.md step 2.
MODE_SAIYAN = "saiyan"
MODE_SUPER_SAIYAN = "super-saiyan"
MODE_BLURB = {
    MODE_SAIYAN: (
        "Saiyan (lite) — keep your existing Hermes runtime; install just the "
        "planner + tier gates + 14 in-process runtimes + 16 SKILL.md files into "
        "your project. No new infrastructure. ~3 minutes."
    ),
    MODE_SUPER_SAIYAN: (
        "Super Saiyan (full) — bring up the full Railway fabric: NATS + Temporal "
        "+ Coordinator + Archon + Admiral. Provisions Tier 2 superagent VPSes on "
        "demand. ~30 minutes start to finish."
    ),
}


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


def bold(s: str) -> str:
    return color(s, "1")


def banner() -> None:
    print()
    print(cyan("⚡ Super Agent — launch wizard"))
    print(cyan("─" * 48))
    print("One repo. Two power levels. The runnable twin of INSTALL.md.")
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


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — pick your power level (Saiyan vs Super Saiyan)
# ─────────────────────────────────────────────────────────────────────────────
def step_mode(env: dict[str, str], cli_mode: str | None, reset: bool) -> str:
    print()
    print(cyan("Step 1 — pick your power level"))
    print()

    if cli_mode in (MODE_SAIYAN, MODE_SUPER_SAIYAN):
        mode = cli_mode
        print(f"  --mode={mode} passed; skipping the question")
    elif env.get("INSTALL_MODE") in (MODE_SAIYAN, MODE_SUPER_SAIYAN) and not reset:
        mode = env["INSTALL_MODE"]
        print(f"  .env already set INSTALL_MODE={mode} (re-run with --reset to change)")
    else:
        print(f"  {bold('Saiyan')}        {MODE_BLURB[MODE_SAIYAN]}")
        print()
        print(f"  {bold('Super Saiyan')}  {MODE_BLURB[MODE_SUPER_SAIYAN]}")
        print()
        print(yellow("  When in doubt, start Saiyan — ~3 min, no infra. Upgrading later"))
        print(yellow("  to Super Saiyan doesn't undo anything."))
        print()
        choice = prompt_choice(
            "  Which path?",
            ["Saiyan (lite)", "Super Saiyan (full)"],
            default_idx=0,
        )
        mode = MODE_SAIYAN if choice.startswith("Saiyan ") else MODE_SUPER_SAIYAN

    env["INSTALL_MODE"] = mode
    print(green(f"  → {mode}"))
    return mode


def _run_hermes_version() -> subprocess.CompletedProcess[str]:
    """Return `hermes --version`, using a login-ish shell if PATH was just updated."""
    if shutil.which("hermes"):
        return subprocess.run(["hermes", "--version"], cwd=ROOT, text=True, capture_output=True)
    return subprocess.run(
        ["bash", "-lc", "hermes --version"], cwd=ROOT, text=True, capture_output=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Hermes preflight
# ─────────────────────────────────────────────────────────────────────────────
def step_hermes_preflight(skip_install: bool) -> bool:
    print()
    print(cyan("Step 2 — Hermes Agent preflight"))
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


def merge_env_file(path: Path, updates: dict[str, str]) -> None:
    """Merge non-empty KEY=VALUE entries into an env file without printing secrets."""
    existing: dict[str, str] = {}
    order: list[str] = []
    if path.exists():
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            existing[key] = value.strip()
            order.append(key)

    for key, value in updates.items():
        if not value:
            continue
        if key not in existing:
            order.append(key)
        existing[key] = value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{key}={existing[key]}" for key in order) + "\n")
    path.chmod(0o600)


def hermes_env_path() -> Path | None:
    result = subprocess.run(
        ["hermes", "config", "env-path"], cwd=ROOT, text=True, capture_output=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — keys & channels (conversational)
# ─────────────────────────────────────────────────────────────────────────────
def step_keys(env: dict[str, str], mode: str, minimal: bool, reset: bool) -> dict[str, str]:
    print()
    print(cyan("Step 3 — keys and channels"))
    print()

    operator = env.get("AGENT_OS_OWNER") if not reset else ""
    if not operator:
        operator = prompt(
            "Operator name (the canonical identity for cross-channel memory)",
            default="justin",
            required=True,
        )
        env["AGENT_OS_OWNER"] = operator

    if not env.get("HERMES_PROVIDER") or reset:
        provider = prompt_choice(
            "Primary Hermes provider:",
            ["openrouter", "anthropic", "openai"],
            default_idx=0,
        )
        env["HERMES_PROVIDER"] = provider

    provider_key = {
        "openrouter": "OPENROUTER_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }.get(env.get("HERMES_PROVIDER", "openrouter"), "OPENROUTER_API_KEY")
    if not env.get(provider_key) or reset:
        env[provider_key] = prompt(
            f"{provider_key} for Hermes {env.get('HERMES_PROVIDER', 'openrouter')}",
            default=env.get(provider_key, ""),
            required=True,
            secret=True,
        )

    if env.get("HERMES_PROVIDER") != "openai" and (not env.get("OPENAI_API_KEY") or reset):
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
            default=env.get("HERMES_DEFAULT_MODEL", "openai/gpt-5.5"),
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

    print()
    print(cyan("Telegram quick access"))
    if not env.get("TELEGRAM_BOT_TOKEN") or reset:
        if prompt_yn("  Configure Telegram now?", default=True):
            print(yellow("  Telegram — create a bot with @BotFather if needed"))
            env["TELEGRAM_BOT_TOKEN"] = prompt("  TELEGRAM_BOT_TOKEN", secret=True)
            env["TELEGRAM_ALLOWED_USERS"] = prompt(
                "  TELEGRAM_ALLOWED_USERS (your numeric Telegram user ID)",
                default=env.get("TELEGRAM_ALLOWED_USERS", ""),
            )

    if minimal:
        return env

    channels: list[str] = []
    print()
    print("Which channels do you want active first?")
    if prompt_yn("  Slack", default=True):
        channels.append("slack")
    if prompt_yn("  Telegram", default=bool(env.get("TELEGRAM_BOT_TOKEN"))):
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
        if not env.get("TELEGRAM_ALLOWED_USERS") or reset:
            env["TELEGRAM_ALLOWED_USERS"] = prompt(
                "  TELEGRAM_ALLOWED_USERS (numeric user ID)",
                default=env.get("TELEGRAM_ALLOWED_USERS", ""),
            )

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
    ]
    # Super Saiyan provisions cloud infra; surface the infra keys for that mode.
    if mode == MODE_SUPER_SAIYAN:
        optional += [
            ("RAILWAY_TOKEN", "Railway — the Super Saiyan fabric runs here"),
            ("DIGITALOCEAN_ACCESS_TOKEN", "DigitalOcean — Tier 2 VPS spawning"),
        ]
    for k, desc in optional:
        if env.get(k) and not reset:
            continue
        if prompt_yn(f"  Configure {k} ({desc})?", default=False):
            env[k] = prompt(f"    {k}", secret=True)

    return env


def step_hermes_config(env: dict[str, str], skip_config: bool) -> bool:
    print()
    print(cyan("Step 4 — configure Hermes itself"))
    print()
    if skip_config:
        print(yellow("  --skip-hermes-config passed; not writing Hermes config/env"))
        return True

    env_path = hermes_env_path()
    if env_path is None:
        print(red("  could not locate Hermes env path; run `hermes setup` manually"))
        return False

    secret_updates = {
        key: env.get(key, "")
        for key in (
            "OPENROUTER_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_ALLOWED_USERS",
            "TELEGRAM_HOME_CHANNEL",
        )
    }
    merge_env_file(env_path, secret_updates)
    print(green(f"  wrote Hermes env secrets to {env_path}"))

    provider = env.get("HERMES_PROVIDER", "").strip()
    model = env.get("HERMES_DEFAULT_MODEL", "").strip()
    config_commands = []
    if provider:
        config_commands.append(["hermes", "config", "set", "model.provider", provider])
    if model:
        config_commands.append(["hermes", "config", "set", "model.default", model])

    for command in config_commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print(red(f"  Hermes command failed: {' '.join(command[:4])}"))
            return False

    if env.get("TELEGRAM_BOT_TOKEN"):
        print("  Telegram token synced. Run `hermes gateway setup` if you want service install.")
    print(green("  Hermes provider/channel config synced"))
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — mode-aware install
# ─────────────────────────────────────────────────────────────────────────────
def _run(cmd: list[str], label: str) -> bool:
    print(f"  running {label} ...")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(red(f"  {label} FAILED — fix and re-run"))
        return False
    print(green(f"  {label} OK"))
    return True


def step_install(env: dict[str, str], mode: str, minimal: bool, skip_install: bool) -> bool:
    print()
    print(cyan(f"Step 5 — install ({mode})"))
    print()

    if skip_install:
        print(yellow("  --skip-install passed; not running the installer"))
        return True

    if mode == MODE_SAIYAN:
        # Drop-in install into an existing Hermes/Python project.
        target = env.get("SAIYAN_TARGET", "")
        if not target:
            target = prompt(
                "  Project root to install the planner + 14 runtimes into",
                default=str(ROOT),
            )
            env["SAIYAN_TARGET"] = target
        installer = ROOT / "install.py"
        if not installer.exists():
            print(red(f"  missing {installer}"))
            return False
        return _run(
            ["python3", str(installer), "--mode=saiyan", f"--target={target}", "--force"],
            "install.py --mode=saiyan",
        )

    # Super Saiyan — full local bring-up; Railway deploy is the final manual step.
    bootstrap = ROOT / "scripts" / "bootstrap.sh"
    if bootstrap.exists():
        if not _run([str(bootstrap)], "scripts/bootstrap.sh"):
            return False
    else:
        print(yellow(f"  missing {bootstrap} — skipping bootstrap"))

    if not minimal:
        if not _run(["uv", "run", "pytest", "-q"], "smoke tests"):
            return False
        if not _run(
            ["uv", "run", "python", "-m", "agent_os.manifest.aggregator"],
            "manifest aggregator",
        ):
            return False

    print()
    print(yellow("  Super Saiyan fabric deploy is the final step:"))
    print(f"    {green('python3 install.py --mode=super-saiyan')}   # or ./scripts/deploy.sh")
    print("  Brings up NATS → Temporal → Coordinator → Archon → Admiral on Railway.")
    return True


def step_summary(env: dict[str, str], mode: str) -> None:
    print()
    print(cyan("─" * 48))
    print(green(f"Super Agent ({mode}) is wired. Hermes launches through the Hermes CLI."))
    print(cyan("─" * 48))
    print()
    print(f"  power level:     {mode}")
    print(f"  operator:        {env.get('AGENT_OS_OWNER', '?')}")
    print(f"  business:        {env.get('BUSINESS_NAME', '?')} — {env.get('BUSINESS_TYPE', '?')}")
    print(f"  workflows:       {env.get('FIRST_WORKFLOWS', '?')}")
    print(f"  default model:   {env.get('HERMES_DEFAULT_MODEL', '?')}")
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
    print(f"  {green('hermes doctor')}            — verify the real Hermes install")
    print(f"  {green('hermes')}                   — start the real Hermes CLI chat")
    print(f"  {green('hermes gateway setup')}     — optional: configure Telegram/Slack")
    if mode == MODE_SUPER_SAIYAN:
        print(
            f"  {green('python3 install.py --mode=super-saiyan')}"
            "  — bring up the Railway fabric"
        )
    print(f"  {green('uv run agent-os manifest')} — refresh the Super Agent system graph")
    print(f"  {green('uv run agent-os explain')}  — query the graph in plain English")
    print()
    print("Mode deep-dive: docs/modes.md. Master prompt twin of this wizard: INSTALL.md.")
    print()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--mode",
        choices=[MODE_SAIYAN, MODE_SUPER_SAIYAN],
        default=None,
        help="pre-pick the power level and skip the question",
    )
    p.add_argument(
        "--minimal",
        action="store_true",
        help="absolute-minimum keys only (provider key, operator, shared brain, Telegram)",
    )
    p.add_argument(
        "--reset",
        action="store_true",
        help="re-prompt for all values, ignoring existing .env",
    )
    p.add_argument("--skip-install", action="store_true", help="skip the mode installer step")
    p.add_argument(
        "--skip-hermes-config",
        action="store_true",
        help="do not sync provider keys or Telegram settings into Hermes config/env",
    )
    p.add_argument(
        "--skip-hermes-install",
        action="store_true",
        help="do not auto-install Hermes Agent if the hermes CLI is missing",
    )
    args = p.parse_args()

    banner()
    env = load_env()

    # Step 1 — power level FIRST, so the rest of the walkthrough can adapt.
    mode = step_mode(env, cli_mode=args.mode, reset=args.reset)

    # Step 2 — Hermes runtime must exist before anything else.
    if not step_hermes_preflight(skip_install=args.skip_hermes_install):
        return 1

    # Step 3 — keys & channels.
    env = step_keys(env, mode=mode, minimal=args.minimal, reset=args.reset)
    write_env(env)

    # Step 4 — push the relevant bits into Hermes' own config.
    if not step_hermes_config(env, skip_config=args.skip_hermes_config):
        return 1

    # Step 5 — mode-aware install.
    if not step_install(env, mode=mode, minimal=args.minimal, skip_install=args.skip_install):
        return 1

    step_summary(env, mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
