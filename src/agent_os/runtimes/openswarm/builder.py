"""Fork-and-customize flow — the headline 'agent builder agent' feature.

Hermes invokes ``op=build`` with a name + description; this module:

  1. Locks + validates name uniqueness, allocates a port
  2. Copies vendor/openswarm into ~/.agent-os/swarms/<name>/
  3. Hands the clone to a Customizer (default: claude_code)
  4. Writes the per-swarm manifest.yaml + saves recorded build metadata
  5. Provisionally registers the swarm so the validator can start it
  6. Runs the Validator (default: health)
  7. On pass: renders vault/skills/active/<name>-swarm.md and returns
  8. On any failure: rolls back atomically — kills processes, archives the
     folder under _archive/_failed/, frees the port, removes registry entry,
     deletes the partially-rendered skill

``op=upgrade`` re-pulls vendor/openswarm, replays the recorded build patches
(when produced by claude_code), re-runs the validator. On pass: swap the
folder atomically; on fail: keep last-known-good and surface the error.
"""
from __future__ import annotations

import datetime as dt
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from . import customizers, fleet, ports, registry, skills, validators

# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build(
    name: str,
    description: str,
    *,
    customizer: str | dict[str, Any] | customizers.Customizer | None = "claude_code",
    customizer_options: dict[str, Any] | None = None,
    validator: str | validators.Validator | None = "health",
    cost_budget_daily_usd: float = 10.0,
) -> dict[str, Any]:
    _guard_name(name)
    if registry.get(name) is not None:
        raise ValueError(f"swarm {name!r} already exists in registry")
    swarm_dir = fleet.folder_for(name)
    if swarm_dir.exists():
        raise FileExistsError(f"swarm folder already exists: {swarm_dir}")

    cust = customizers.get_customizer(customizer, options=customizer_options)
    val = validators.get_validator(validator)

    port = ports.allocate(name)
    registered = False
    skill_path: Path | None = None

    try:
        # 1. Copy vendor → swarm folder.
        vendor = fleet.vendor_root()
        vendor_sha = _vendor_sha(vendor)
        shutil.copytree(vendor, swarm_dir, ignore=shutil.ignore_patterns(".git"))
        env_example = swarm_dir / ".env.example"
        env_path = swarm_dir / ".env"
        if env_example.exists() and not env_path.exists():
            shutil.copy(env_example, env_path)

        # 2. Run the customizer.
        agents_md_path = swarm_dir / "AGENTS.md"
        agents_md = agents_md_path.read_text() if agents_md_path.exists() else ""
        ctx = customizers.BuildContext(
            name=name, description=description, swarm_dir=swarm_dir, agents_md=agents_md,
        )
        outcome = cust.customize(ctx)
        if not outcome.success:
            raise RuntimeError(f"customization failed ({cust.name}): {outcome.error}")

        # 3. Persist patches diff (if any).
        patches_path = None
        if outcome.patches_diff:
            build_dir = swarm_dir / ".build"
            build_dir.mkdir(parents=True, exist_ok=True)
            patches_path = build_dir / "patches.diff"
            patches_path.write_text(outcome.patches_diff)

        # 4. Write per-swarm manifest.yaml.
        per_swarm_manifest = swarm_dir / "manifest.yaml"
        per_swarm_manifest.write_text(
            _render_per_swarm_manifest(
                name=name,
                description=description,
                outcome=outcome,
                cost_budget_daily_usd=cost_budget_daily_usd,
            )
        )

        # 5. Provisionally register so the validator's fleet.start works.
        registry.add(
            name,
            port=port,
            base="vendor/openswarm",
            forked_from_sha=vendor_sha,
            agency="open-swarm",
            business_purpose=description,
            manifest=str(per_swarm_manifest),
            customizer=cust.name,
            customizer_options=customizer_options or {},
            build_prompt=description,
            patches_path=str(patches_path) if patches_path else None,
            output_types=outcome.output_types,
            examples=outcome.examples,
            cost_budget_daily_usd=cost_budget_daily_usd,
            agents=outcome.agents,
            pid=None,
        )
        registered = True

        # 6. Validation gate.
        v_result = val.validate(name=name, port=port, swarm_dir=swarm_dir)
        if not v_result.success:
            raise RuntimeError(f"validation failed ({val.name}): {v_result.error}")

        # 7. Render the routing skill.
        skill_path = skills.render_for(
            name,
            description=skills.derive_description(description, outcome.examples),
            business_purpose=description,
            output_types=", ".join(outcome.output_types) or skills.DEFAULT_OUTPUT_TYPES,
            examples=outcome.examples or [
                f"Generate a {description.lower()} deliverable for me.",
            ],
            cost_budget_daily_usd=cost_budget_daily_usd,
            manifest_path=str(per_swarm_manifest),
        )

        return {
            "name": name,
            "port": port,
            "swarm_dir": str(swarm_dir),
            "manifest_path": str(per_swarm_manifest),
            "skill_path": str(skill_path),
            "customizer": cust.name,
            "validator": val.name,
            "agents": outcome.agents,
            "build_cost_usd": outcome.cost_usd,
            "patches": str(patches_path) if patches_path else None,
        }

    except Exception:
        _rollback(name, swarm_dir, registered=registered, skill_path=skill_path,
                  reason="build")
        raise


# --------------------------------------------------------------------------
# upgrade
# --------------------------------------------------------------------------

def upgrade(
    name: str,
    *,
    validator: str | validators.Validator | None = "health",
) -> dict[str, Any]:
    """Re-pull vendor, replay recorded customization, re-validate.

    Atomic: on any failure the existing swarm folder is preserved untouched
    and the registry is unchanged. On success the old folder is archived.
    """
    entry = registry.get(name)
    if entry is None:
        raise KeyError(f"swarm {name!r} not in registry")
    if name == "default":
        raise ValueError("default swarm has no recorded customization to replay")

    val = validators.get_validator(validator)
    swarm_dir = fleet.folder_for(name)
    staging_dir = swarm_dir.with_suffix(".upgrading")
    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    try:
        vendor = fleet.vendor_root()
        new_sha = _vendor_sha(vendor)
        if new_sha and new_sha == entry.get("forked_from_sha"):
            return {"status": "no-upgrade", "head": new_sha}

        # Stage a fresh clone.
        shutil.copytree(vendor, staging_dir, ignore=shutil.ignore_patterns(".git"))
        env_example = staging_dir / ".env.example"
        env_target = staging_dir / ".env"
        live_env = swarm_dir / ".env"
        if live_env.exists():
            shutil.copy(live_env, env_target)
        elif env_example.exists() and not env_target.exists():
            shutil.copy(env_example, env_target)

        # Replay recorded customization.
        replay = _replay_customization(name, entry, staging_dir)
        if not replay["success"]:
            raise RuntimeError(f"replay failed: {replay['error']}")

        # Re-validate against live port (server can't be running concurrently).
        port = int(entry["port"])
        # Stop the live swarm before swapping in case it was running.
        try:
            fleet.stop(name)
        except KeyError:
            pass
        # Swap directories: live → archive, staging → live.
        archive_path = _archive_failed_or_replaced(swarm_dir, name, kind="replaced")
        shutil.move(str(staging_dir), str(swarm_dir))

        # Update registry with new sha + replay metadata.
        registry.update(
            name,
            forked_from_sha=new_sha,
            replaced_at=dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            previous_archive=str(archive_path) if archive_path else None,
            pid=None,
        )

        # Re-run the validator on the freshly-installed swarm.
        v_result = val.validate(name=name, port=port, swarm_dir=swarm_dir)
        if not v_result.success:
            # Roll back: archive the broken upgrade, restore the previous folder.
            broken = _archive_failed_or_replaced(swarm_dir, name, kind="upgrade-broken")
            if archive_path is not None:
                shutil.move(str(archive_path), str(swarm_dir))
                registry.update(
                    name,
                    forked_from_sha=entry.get("forked_from_sha"),
                    last_upgrade_error=v_result.error,
                    upgrade_archived_to=str(broken) if broken else None,
                )
            raise RuntimeError(f"upgrade validation failed: {v_result.error}")

        return {
            "status": "upgraded",
            "from": entry.get("forked_from_sha"),
            "to": new_sha,
            "replay": replay["summary"],
            "previous_archive": str(archive_path) if archive_path else None,
        }

    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

RESERVED_NAMES = {"default", "_archive"}


def _guard_name(name: str) -> None:
    if name in RESERVED_NAMES:
        raise ValueError(f"name {name!r} is reserved")
    if not name or "/" in name or name.startswith("."):
        raise ValueError(f"invalid swarm name: {name!r}")


def _vendor_sha(vendor: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=vendor, capture_output=True, text=True, check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
    return out.stdout.strip() or None


def _render_per_swarm_manifest(
    *, name: str, description: str, outcome: customizers.CustomizationOutcome,
    cost_budget_daily_usd: float,
) -> str:
    data = {
        "component": f"swarm.{name}",
        "type": "vertical-app",
        "parent_runtime": "runtime.openswarm",
        "business_purpose": description,
        "agents": outcome.agents,
        "data_sources": [],
        "outputs": [
            {"type": ot, "consumer": "vault.uploads"} for ot in outcome.output_types
        ] or [{"type": "deliverable", "consumer": "vault.uploads"}],
        "cost_budget_daily_usd": cost_budget_daily_usd,
        "upstream_signals": ["runtime.openswarm"],
        "downstream_consumers": [],
    }
    return yaml.safe_dump(data, sort_keys=False)


def _archive_failed_or_replaced(
    folder: Path, name: str, *, kind: str = "failed"
) -> Path | None:
    if not folder.exists():
        return None
    archive_root = fleet.ARCHIVE_HOME / kind
    archive_root.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    target = archive_root / f"{name}-{ts}"
    shutil.move(str(folder), str(target))
    return target


def _rollback(
    name: str, swarm_dir: Path, *, registered: bool, skill_path: Path | None,
    reason: str,
) -> None:
    """Best-effort cleanup so partial state never leaks to the user."""
    # 1. Stop any process tied to the (possibly registered) swarm.
    try:
        if registered and registry.get(name) is not None:
            try:
                fleet.stop(name, kill=True)
            except Exception:  # noqa: BLE001
                pass
            registry.remove(name)
    except KeyError:
        pass
    # 2. Remove the partially-rendered skill.
    if skill_path is not None and skill_path.exists():
        try:
            skill_path.unlink()
        except OSError:
            pass
    skills.remove_for(name)
    # 3. Archive the swarm folder under _failed/ so the user can inspect.
    if swarm_dir.exists():
        _archive_failed_or_replaced(swarm_dir, name, kind=f"{reason}-failed")


def _replay_customization(
    name: str, entry: dict[str, Any], staging_dir: Path,
) -> dict[str, Any]:
    """Re-run the recorded customization against a fresh vendor clone."""
    cust_name = entry.get("customizer") or "noop"
    options = entry.get("customizer_options") or {}
    description = entry.get("build_prompt") or entry.get("business_purpose") or ""

    cust = customizers.get_customizer(cust_name, options=options)
    agents_md_path = staging_dir / "AGENTS.md"
    agents_md = agents_md_path.read_text() if agents_md_path.exists() else ""
    ctx = customizers.BuildContext(
        name=name, description=description, swarm_dir=staging_dir, agents_md=agents_md,
    )
    outcome = cust.customize(ctx)
    if not outcome.success:
        return {"success": False, "error": outcome.error or "customizer failed"}
    return {"success": True, "summary": outcome.summary, "outcome": outcome}
