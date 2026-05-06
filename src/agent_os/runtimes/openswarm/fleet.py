"""Multi-instance manager for forked OpenSwarm servers.

Each registered swarm = its own folder, port, .env, .venv, manifest. Fleet
operations are idempotent and resilient to crashed processes via PID checks
+ port-bind probes.
"""
from __future__ import annotations

import datetime as dt
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from . import http_client, ports, registry

SWARMS_HOME = Path(os.environ.get("OPENSWARM_HOME", "~/.agent-os/swarms")).expanduser()
ARCHIVE_HOME = SWARMS_HOME / "_archive"
VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve()
RUNS_ROOT = VAULT_ROOT / "runs" / "openswarm"
GRAPH_ROOT = VAULT_ROOT / "graph"
DEFAULT_AGENCY = "open-swarm"
START_TIMEOUT_S = 60.0
START_POLL_S = 0.5
DEFAULT_IDLE_HIBERNATE_MIN = float(os.environ.get("OPENSWARM_IDLE_HIBERNATE_MIN", "0"))
SOFT_BUDGET_PCT = 0.80


class BudgetExceeded(RuntimeError):
    """Raised when a run would exceed a swarm's daily cost budget."""


# ---------- folder layout ----------

def folder_for(name: str) -> Path:
    return SWARMS_HOME / name


def vendor_root() -> Path:
    """Resolve vendor/openswarm. Overridable via OPENSWARM_VENDOR_ROOT for tests
    and for pinning per-swarm to a different upstream commit."""
    override = os.environ.get("OPENSWARM_VENDOR_ROOT")
    if override:
        path = Path(override).expanduser()
        if not path.exists():
            raise RuntimeError(f"OPENSWARM_VENDOR_ROOT={override!r} does not exist")
        return path
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "vendor" / "openswarm"
        if candidate.exists():
            return candidate
    raise RuntimeError("vendor/openswarm not found — did you `git submodule update --init`?")


_vendor_root = vendor_root  # backwards compat — internal callers


# ---------- liveness ----------

def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    return True


def _live_status(entry: dict[str, Any]) -> str:
    pid = entry.get("pid")
    port = entry.get("port")
    if _pid_alive(pid) and port and http_client.health(int(port)):
        return "running"
    if _pid_alive(pid):
        return "starting-or-unhealthy"
    if pid:
        return "crashed"
    return "stopped"


# ---------- provisioning ----------

def provision_default(*, force: bool = False) -> dict[str, Any]:
    """Materialize the `default` swarm by copying vendor/openswarm to ~/.agent-os/swarms/default/.

    Idempotent: if folder + registry entry exist, returns them. With force=True,
    archives the existing folder and re-copies.
    """
    name = "default"
    folder = folder_for(name)
    existing = registry.get(name)
    if existing and folder.exists() and not force:
        return existing
    if force and folder.exists():
        archive_path = _archive(folder, name)
        if existing:
            registry.update(name, archived_to=str(archive_path), pid=None)
    SWARMS_HOME.mkdir(parents=True, exist_ok=True)
    if not folder.exists():
        shutil.copytree(vendor_root(), folder, ignore=shutil.ignore_patterns(".git"))
        env_example = folder / ".env.example"
        env_path = folder / ".env"
        if env_example.exists() and not env_path.exists():
            env_path.write_text(env_example.read_text())
    if existing:
        return registry.update(name, port=existing.get("port") or ports.allocate(name))
    port = ports.allocate(name)
    return registry.add(
        name,
        port=port,
        base="vendor/openswarm",
        agency=DEFAULT_AGENCY,
        business_purpose="default OpenSwarm — general multi-agent production",
        manifest=str(folder / "manifest.yaml"),
        pid=None,
    )


# ---------- start / stop ----------

def start(name: str) -> dict[str, Any]:
    entry = registry.get(name) or (provision_default() if name == "default" else None)
    if entry is None:
        raise KeyError(f"unknown swarm: {name!r}")
    if _live_status(entry) == "running":
        return registry.get(name)  # already up

    folder = folder_for(name)
    if not folder.exists():
        raise RuntimeError(f"swarm folder missing: {folder}")
    port = int(entry["port"])

    log_dir = folder / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"server-{int(time.time())}.log"

    env = os.environ.copy()
    dotenv = folder / ".env"
    if dotenv.exists():
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    env["PORT"] = str(port)

    log_fh = log_path.open("w")
    venv_python = folder / ".venv" / "bin" / "python"
    python = str(venv_python) if venv_python.exists() else "python"
    proc = subprocess.Popen(
        [python, "server.py"],
        cwd=str(folder),
        env=env,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    deadline = time.time() + START_TIMEOUT_S
    while time.time() < deadline:
        if proc.poll() is not None:
            registry.update(name, pid=None, last_error=f"exited rc={proc.returncode}",
                            log=str(log_path))
            raise RuntimeError(
                f"swarm {name!r} server exited rc={proc.returncode}; see {log_path}"
            )
        if http_client.health(port):
            return registry.update(
                name,
                pid=proc.pid,
                started_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
                log=str(log_path),
            )
        time.sleep(START_POLL_S)

    # timeout — leave process running so user can debug, but mark unhealthy
    registry.update(name, pid=proc.pid, log=str(log_path),
                    last_error="health check timed out")
    raise TimeoutError(f"swarm {name!r} did not become healthy within {START_TIMEOUT_S}s")


def stop(name: str, *, kill: bool = False) -> dict[str, Any]:
    entry = registry.get(name)
    if entry is None:
        raise KeyError(name)
    pid = entry.get("pid")
    if pid and _pid_alive(pid):
        sig = signal.SIGKILL if kill else signal.SIGTERM
        try:
            os.killpg(os.getpgid(int(pid)), sig)
        except (ProcessLookupError, PermissionError):
            try:
                os.kill(int(pid), sig)
            except ProcessLookupError:
                pass
        # brief grace period
        for _ in range(20):
            if not _pid_alive(pid):
                break
            time.sleep(0.1)
    return registry.update(name, pid=None,
                           stopped_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))


def restart(name: str) -> dict[str, Any]:
    stop(name)
    return start(name)


# ---------- run ----------

def run(*, swarm: str = "default", agent: str = "auto", prompt: str,
        files: list[str] | None = None) -> dict[str, Any]:
    entry = registry.get(swarm)
    if entry is None and swarm == "default":
        entry = provision_default()
    if entry is None:
        raise KeyError(f"unknown swarm: {swarm!r}")

    # Pre-flight cost guard. Soft-warn at 80% of daily budget; hard-block at 100%.
    cost_warning = _check_budget(swarm, entry)

    if _live_status(entry) != "running":
        start(swarm)
        entry = registry.get(swarm)

    port = int(entry["port"])
    agency = entry.get("agency", DEFAULT_AGENCY)
    response = http_client.get_completion(
        port,
        agency=agency,
        message=prompt,
        attachments=files,
        agent=agent,
    )
    registry.update(swarm,
                    last_run=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"))
    out: dict[str, Any] = {"swarm": swarm, "agent": agent, "port": port, "response": response}
    if cost_warning:
        out["cost_warning"] = cost_warning
    return out


# ---------- discovery ----------

def list_swarms() -> list[dict[str, Any]]:
    out = []
    for name, entry in registry.list_all().items():
        out.append({"name": name, **entry, "live_status": _live_status(entry)})
    return out


def status(name: str | None = None) -> dict[str, Any]:
    if name is None:
        return {"fleet": list_swarms()}
    entry = registry.get(name)
    if entry is None:
        raise KeyError(name)
    return {"name": name, **entry, "live_status": _live_status(entry)}


# ---------- destroy / archive ----------

def _archive(folder: Path, name: str) -> Path:
    ARCHIVE_HOME.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    target = ARCHIVE_HOME / f"{name}-{ts}"
    shutil.move(str(folder), str(target))
    return target


def destroy(name: str) -> dict[str, Any]:
    """Stop, archive folder, remove from registry, leave skill removal to caller."""
    entry = registry.get(name)
    if entry is None:
        raise KeyError(name)
    if entry.get("pid") and _pid_alive(entry["pid"]):
        stop(name)
    folder = folder_for(name)
    archived_to = _archive(folder, name) if folder.exists() else None
    registry.remove(name)
    return {"name": name, "archived_to": str(archived_to) if archived_to else None}


# ---------- recovery ----------

def cleanup_orphans() -> dict[str, Any]:
    """Reconcile registry with live OS state. Marks crashed pids as None."""
    fixed: list[str] = []
    for name, entry in registry.list_all().items():
        pid = entry.get("pid")
        if pid and not _pid_alive(pid):
            registry.update(name, pid=None, last_error="orphaned")
            fixed.append(name)
    return {"reconciled": fixed}


# ---------- cost rollups ----------

def cost_rollup(swarm: str | None = None, *, days: int = 1) -> dict[str, Any]:
    """Sum cost_usd from vault/runs/openswarm/*.yaml inside the time window.

    OpenSwarm's HTTP responses do not yet emit cost data, so totals will read
    as 0 until upstream wires cost reporting through. The aggregation contract
    is forward-compatible: when costs start landing in artifacts (top-level
    ``cost_usd`` or nested under ``output.response.cost_usd``), this function
    will surface them per-swarm without further change.

    If ``swarm`` is None, returns a dict keyed by swarm name. The synthetic
    key ``"_unknown"`` collects artifacts whose output omits a swarm field.
    """
    cutoff = time.time() - days * 86400
    by_swarm: dict[str, dict[str, float]] = {}
    if not RUNS_ROOT.exists():
        if swarm is not None:
            return {"swarm": swarm, "window_days": days, "cost_usd": 0.0, "runs": 0}
        return {"window_days": days, "swarms": {}}

    for path in sorted(RUNS_ROOT.glob("*.yaml")):
        try:
            if path.stat().st_mtime < cutoff:
                continue
            data = yaml.safe_load(path.read_text()) or {}
        except (OSError, yaml.YAMLError):
            continue
        s = _swarm_from_artifact(data) or "_unknown"
        bucket = by_swarm.setdefault(s, {"cost_usd": 0.0, "runs": 0})
        bucket["runs"] += 1
        bucket["cost_usd"] += _cost_from_artifact(data)

    if swarm is not None:
        return {
            "swarm": swarm,
            "window_days": days,
            **by_swarm.get(swarm, {"cost_usd": 0.0, "runs": 0}),
        }
    return {"window_days": days, "swarms": by_swarm}


def _swarm_from_artifact(data: dict[str, Any]) -> str | None:
    out = data.get("output") or {}
    if isinstance(out, dict):
        return out.get("swarm")
    return None


def _cost_from_artifact(data: dict[str, Any]) -> float:
    top = data.get("cost_usd")
    if isinstance(top, (int, float)) and top:
        return float(top)
    out = data.get("output") or {}
    if isinstance(out, dict):
        for path_keys in (("cost_usd",), ("response", "cost_usd")):
            cur: Any = out
            for k in path_keys:
                if not isinstance(cur, dict):
                    cur = None
                    break
                cur = cur.get(k)
            if isinstance(cur, (int, float)) and cur:
                return float(cur)
    return 0.0


def _check_budget(swarm: str, entry: dict[str, Any]) -> str | None:
    """Return a warning string if at >= soft threshold; raise BudgetExceeded
    when over budget. Returns None below the soft threshold."""
    budget = entry.get("cost_budget_daily_usd")
    if not budget or budget <= 0:
        return None
    today = cost_rollup(swarm, days=1).get("cost_usd", 0.0)
    if today >= budget:
        raise BudgetExceeded(
            f"swarm {swarm!r} daily budget ${budget:.2f} exceeded "
            f"(spent ${today:.2f}). Adjust cost_budget_daily_usd or wait."
        )
    if today >= budget * SOFT_BUDGET_PCT:
        return f"approaching daily budget: ${today:.2f}/${budget:.2f}"
    return None


# ---------- idle hibernation ----------

def hibernate_idle(*, default_minutes: float | None = None) -> dict[str, Any]:
    """Stop swarms that haven't been used in their idle window.

    A swarm's threshold = ``idle_hibernate_minutes`` from its registry entry,
    falling back to ``default_minutes`` (default ``OPENSWARM_IDLE_HIBERNATE_MIN``
    env, default 0 = never hibernate). 0 disables hibernation for that swarm.
    """
    threshold_default = (
        default_minutes if default_minutes is not None else DEFAULT_IDLE_HIBERNATE_MIN
    )
    hibernated: list[str] = []
    skipped: list[str] = []
    now = dt.datetime.now(dt.UTC)
    for name, entry in registry.list_all().items():
        threshold = float(entry.get("idle_hibernate_minutes", threshold_default))
        if threshold <= 0:
            skipped.append(name)
            continue
        if not entry.get("pid") or not _pid_alive(entry["pid"]):
            continue  # already not running
        last_run_iso = entry.get("last_run") or entry.get("started_at")
        if not last_run_iso:
            continue
        try:
            last_run = dt.datetime.fromisoformat(last_run_iso)
        except ValueError:
            continue
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=dt.UTC)
        idle_minutes = (now - last_run).total_seconds() / 60.0
        if idle_minutes >= threshold:
            try:
                stop(name)
                hibernated.append(name)
            except KeyError:
                pass
    return {"hibernated": hibernated, "skipped": skipped}


# ---------- snapshot for the dashboard ----------

def snapshot_json(*, write: bool = True) -> dict[str, Any]:
    """Build a dashboard-friendly JSON snapshot of the fleet.

    When ``write=True`` (default), persists to ``vault/graph/openswarm.json``
    so the Next.js dashboard can read it from the same vault path used by the
    rest of the system. The function is idempotent — caller can poll it.
    """
    swarms = []
    for name, entry in registry.list_all().items():
        rollup = cost_rollup(name, days=1)
        swarms.append({
            "name": name,
            "port": entry.get("port"),
            "agency": entry.get("agency", DEFAULT_AGENCY),
            "business_purpose": entry.get("business_purpose", ""),
            "customizer": entry.get("customizer", "noop"),
            "live_status": _live_status(entry),
            "last_run": entry.get("last_run"),
            "started_at": entry.get("started_at"),
            "cost_budget_daily_usd": entry.get("cost_budget_daily_usd"),
            "cost_today_usd": rollup.get("cost_usd", 0.0),
            "runs_today": rollup.get("runs", 0),
        })
    snapshot = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "fleet": sorted(swarms, key=lambda s: s["name"]),
    }
    if write:
        GRAPH_ROOT.mkdir(parents=True, exist_ok=True)
        path = GRAPH_ROOT / "openswarm.json"
        import json
        path.write_text(json.dumps(snapshot, indent=2))
        snapshot["written_to"] = str(path)
    return snapshot


# ---------- composition (Phase D) ----------

def pipeline(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Run a sequence of swarm calls, threading each result into the next.

    Each step shape::

        {"swarm": "seo-swarm", "agent": "auto" (default), "prompt": "...{prev}..."}

    The literal substring ``{prev}`` in a step's prompt is replaced with the
    previous step's response payload (str-coerced). The first step ignores
    ``{prev}`` and any unfilled placeholder is left untouched.

    Returns ``{"steps": [step_results...], "final": last_step_result}``.
    """
    if not steps:
        return {"steps": [], "final": None}
    results: list[dict[str, Any]] = []
    prev_text = ""
    for i, step in enumerate(steps):
        prompt = step.get("prompt", "")
        if "{prev}" in prompt:
            prompt = prompt.replace("{prev}", prev_text)
        result = run(
            swarm=step.get("swarm", "default"),
            agent=step.get("agent", "auto"),
            prompt=prompt,
            files=step.get("files"),
        )
        results.append({"step": i, "swarm": step.get("swarm", "default"), **result})
        prev_text = _result_text(result)
    return {"steps": results, "final": results[-1] if results else None}


def _result_text(result: dict[str, Any]) -> str:
    response = result.get("response")
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        for key in ("text", "content", "message", "answer"):
            v = response.get(key)
            if isinstance(v, str):
                return v
        try:
            import json
            return json.dumps(response)
        except (TypeError, ValueError):
            return str(response)
    return str(response or "")


def fan_out(
    *,
    swarm: str,
    prompts: list[str],
    agent: str = "auto",
    concurrency: int = 4,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Run the same swarm with N prompts in parallel.

    Returns ``{"results": [...], "errors": [...]}`` where ``results`` preserves
    input order. Each entry is either a successful run dict or
    ``{"error": "...", "prompt_index": i}``. Concurrency is bounded by
    ``concurrency``; OpenSwarm's FastAPI handles concurrent requests.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not prompts:
        return {"results": [], "errors": []}

    indexed: list[tuple[int, str]] = list(enumerate(prompts))
    out: list[dict[str, Any] | None] = [None] * len(prompts)
    errors: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = {
            pool.submit(run, swarm=swarm, agent=agent, prompt=p, files=files): i
            for i, p in indexed
        }
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                out[i] = fut.result()
            except Exception as e:  # noqa: BLE001
                err = {"error": f"{type(e).__name__}: {e}", "prompt_index": i}
                errors.append(err)
                out[i] = err
    return {"results": out, "errors": errors}
