"""SSH bootstrap — installs and starts Hermes on a freshly provisioned VPS.

Steps:
  1. Connect to VPS over SSH (Paramiko)
  2. apt install: git, curl, tmux, build-essential
  3. Install uv
  4. git clone hermes-super-agent repo
  5. uv sync
  6. Render and write AGENT.md from Jinja2 template
  7. Start Hermes in a tmux session with env vars injected (never written to disk)
  8. Poll /health until 200 OK

Usage:
    from agent_os.orchestrator.bootstrap import bootstrap
    result = await bootstrap(agent_id=..., vps_ip=..., mission=..., metadata={...})
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

_REPO_URL = os.getenv("HERMES_REPO_URL", "https://github.com/jbellsolutions/hermes-super-agent")
_SSH_KEY_PATH = os.getenv("SSH_PRIVATE_KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))
_SSH_USER = os.getenv("VPS_SSH_USER", "root")
_A2A_PORT = int(os.getenv("HERMES_A2A_PORT", "8080"))
_HEALTH_TIMEOUT = 180  # seconds to wait for /health OK


async def bootstrap(
    agent_id: str,
    vps_ip: str,
    mission: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bootstrap Hermes on the given VPS IP. Returns status dict."""
    metadata = metadata or {}
    t0 = time.monotonic()

    try:
        import paramiko
    except ImportError:
        logger.warning("paramiko not installed — returning dev stub for bootstrap")
        return _stub_result(agent_id, vps_ip, t0, note="paramiko not installed")

    model = metadata.get("model", "deepseek-v4-pro")
    branch = metadata.get("branch", "main")
    env_vars = _collect_env_vars(metadata)

    # Render AGENT.md from Jinja2 template
    agent_md = _render_agent_md(agent_id=agent_id, mission=mission, model=model, metadata=metadata)

    # Render bootstrap.sh
    bootstrap_sh = _render_bootstrap_sh(
        agent_id=agent_id,
        vps_ip=vps_ip,
        agent_md_content=agent_md,
        branch=branch,
        nats_url=env_vars.get("NATS_URL", ""),
        install_node=metadata.get("install_node", True),
        install_docker=metadata.get("install_docker", True),
        install_aider=metadata.get("install_aider", True),
    )

    # Run via SSH in executor (paramiko is sync)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _ssh_bootstrap,
        vps_ip,
        bootstrap_sh,
        env_vars,
        agent_id,
    )

    if result.get("status") == "error":
        return {**result, "elapsed_seconds": time.monotonic() - t0}

    # Poll /health
    healthy = await _wait_for_health(vps_ip, _A2A_PORT)
    if not healthy:
        return {
            "status": "error",
            "error": f"Hermes /health did not return 200 within {_HEALTH_TIMEOUT}s",
            "elapsed_seconds": time.monotonic() - t0,
        }

    return {
        "status": "completed",
        "agent_id": agent_id,
        "vps_ip": vps_ip,
        "a2a_port": _A2A_PORT,
        "elapsed_seconds": time.monotonic() - t0,
    }


def _ssh_bootstrap(
    vps_ip: str,
    bootstrap_sh: str,
    env_vars: dict[str, str],
    agent_id: str,
) -> dict[str, Any]:
    """Synchronous SSH session — runs bootstrap.sh on the remote VPS."""
    import paramiko

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=vps_ip,
            username=_SSH_USER,
            key_filename=_SSH_KEY_PATH,
            timeout=30,
            banner_timeout=60,
        )
    except Exception as exc:
        logger.error("SSH connect to %s failed: %s", vps_ip, exc)
        return {"status": "error", "error": f"SSH connect failed: {exc}"}

    # Upload bootstrap.sh via SFTP
    sftp = client.open_sftp()
    remote_path = f"/tmp/bootstrap-{agent_id}.sh"
    try:
        with sftp.file(remote_path, "w") as f:
            f.write(bootstrap_sh)
        sftp.chmod(remote_path, 0o755)
    finally:
        sftp.close()

    # Build env var export string (injected at process level, not written to disk)
    env_export = " ".join(f'{k}="{v}"' for k, v in env_vars.items())
    cmd = f"env {env_export} bash {remote_path} 2>&1"

    logger.info("Running bootstrap on %s for agent %s", vps_ip, agent_id)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
    stdin.close()

    output_lines = []
    for line in stdout:
        line = line.rstrip()
        output_lines.append(line)
        logger.debug("[%s] %s", agent_id, line)

    exit_code = stdout.channel.recv_exit_status()
    client.close()

    if exit_code != 0:
        tail = "\n".join(output_lines[-20:])
        return {
            "status": "error",
            "error": f"bootstrap.sh exited {exit_code}. Last output:\n{tail}",
        }

    return {"status": "completed", "output_lines": len(output_lines)}


async def _wait_for_health(vps_ip: str, port: int) -> bool:
    """Poll http://{vps_ip}:{port}/health until 200 or timeout."""
    import httpx

    url = f"http://{vps_ip}:{port}/health"
    deadline = time.monotonic() + _HEALTH_TIMEOUT

    while time.monotonic() < deadline:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    logger.info("Hermes healthy at %s", url)
                    return True
        except httpx.HTTPError:
            pass
        await asyncio.sleep(5)

    return False


def _render_agent_md(
    agent_id: str,
    mission: str,
    model: str,
    metadata: dict[str, Any],
) -> str:
    """Render AGENT.md from templates/AGENT.md.j2."""
    try:
        from jinja2 import Environment, FileSystemLoader
        templates_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates")
        )
        env = Environment(loader=FileSystemLoader(templates_dir))
        tpl = env.get_template("AGENT.md.j2")
        return tpl.render(
            agent_id=agent_id,
            mission=mission,
            model=model,
            role=metadata.get("role", "Specialist"),
            created_at=_now_iso(),
            created_by="Admiral Hermes",
            capabilities=metadata.get("capabilities", ["Execute delegated tasks", "Publish NATS events"]),
            tools_allowed=metadata.get("tools_allowed", ["hermes_self", "terminal"]),
            tools_denied=metadata.get("tools_denied", []),
            tier_ceiling=metadata.get("tier_ceiling", 2),
            daily_budget=metadata.get("daily_budget", "10.00"),
            per_task_ceiling=metadata.get("per_task_ceiling", "2.00"),
            control_level=metadata.get("control_level", "delegated-autonomy"),
            sub_fleet=metadata.get("sub_fleet", []),
            a2a_base_url=f"http://localhost:{_A2A_PORT}",
            env_vars={},
            notes=metadata.get("notes", ""),
        )
    except Exception as exc:
        logger.warning("Jinja2 template render failed (%s) — using minimal AGENT.md", exc)
        return f"# Agent Identity — {agent_id}\n\n## Mission\n{mission}\n\n## Model\n{model}\n"


def _render_bootstrap_sh(
    agent_id: str,
    vps_ip: str,
    agent_md_content: str,
    branch: str = "main",
    nats_url: str = "",
    install_node: bool = True,
    install_docker: bool = True,
    install_aider: bool = True,
) -> str:
    """Render bootstrap.sh from templates/bootstrap.sh.j2."""
    try:
        from jinja2 import Environment, FileSystemLoader
        templates_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates")
        )
        env = Environment(loader=FileSystemLoader(templates_dir))
        tpl = env.get_template("bootstrap.sh.j2")
        return tpl.render(
            agent_id=agent_id,
            vps_ip=vps_ip,
            repo_url=_REPO_URL,
            branch=branch,
            install_dir="/opt/hermes",
            agent_md_content=agent_md_content,
            a2a_port=_A2A_PORT,
            nats_url=nats_url,
            generated_at=_now_iso(),
            install_node=install_node,
            install_docker=install_docker,
            install_aider=install_aider,
        )
    except Exception as exc:
        logger.warning("bootstrap.sh template render failed (%s) — using inline script", exc)
        return _inline_bootstrap(agent_id, agent_md_content)


def _inline_bootstrap(agent_id: str, agent_md_content: str) -> str:
    """Minimal inline bootstrap script used when Jinja2 template fails."""
    # Escape single quotes in agent_md_content
    escaped = agent_md_content.replace("'", "'\"'\"'")
    return f"""#!/usr/bin/env bash
set -euo pipefail
apt-get update -qq && apt-get install -y --no-install-recommends git curl tmux build-essential
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
git clone --branch main --depth 1 {_REPO_URL} /opt/hermes
cd /opt/hermes && uv sync --no-dev
cat > /opt/hermes/AGENT.md << 'EOF'
{escaped}
EOF
tmux kill-session -t {agent_id} 2>/dev/null || true
tmux new-session -d -s {agent_id} 'cd /opt/hermes && uv run hermes 2>&1 | tee /opt/hermes/hermes.log'
"""


def _collect_env_vars(metadata: dict[str, Any]) -> dict[str, str]:
    """Build env var dict to inject into the bootstrap process.

    Reads from metadata['env_vars'] dict plus falls back to Admiral's own env.
    Secrets are injected at SSH process level — never written to disk.
    """
    vars_to_forward = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "NATS_URL",
        "TEMPORAL_HOST",
        "COORDINATOR_URL",
        "COORDINATOR_DEFAULT_MODEL",
        "MOONSHOT_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENROUTER_API_KEY",
        "GOOGLE_API_KEY",
        "RETELL_API_KEY",
        "RETELL_AGENT_ID",
        "INSTANTLY_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    ]

    env: dict[str, str] = {}
    for key in vars_to_forward:
        val = os.getenv(key, "")
        if val:
            env[key] = val

    # Override / add from metadata
    for k, v in (metadata.get("env_vars") or {}).items():
        env[str(k)] = str(v)

    return env


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _stub_result(agent_id: str, vps_ip: str, t0: float, note: str = "") -> dict[str, Any]:
    return {
        "status": "completed",
        "agent_id": agent_id,
        "vps_ip": vps_ip,
        "a2a_port": _A2A_PORT,
        "elapsed_seconds": time.monotonic() - t0,
        "note": f"dev stub — {note}",
    }
