"""File-locked YAML registry for the OpenSwarm fleet."""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import os
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path(
    os.environ.get("OPENSWARM_REGISTRY", "~/.agent-os/swarms/registry.yaml")
).expanduser()


def _ensure_parent() -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextlib.contextmanager
def _locked():
    """Acquire an exclusive flock on the registry while reading/writing."""
    _ensure_parent()
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text("swarms: {}\n")
    with REGISTRY_PATH.open("r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield fh
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _load(fh) -> dict[str, Any]:
    fh.seek(0)
    raw = fh.read()
    data = yaml.safe_load(raw) or {}
    if "swarms" not in data:
        data["swarms"] = {}
    return data


def _save(fh, data: dict[str, Any]) -> None:
    fh.seek(0)
    fh.truncate()
    yaml.safe_dump(data, fh, sort_keys=False)


def list_all() -> dict[str, dict[str, Any]]:
    with _locked() as fh:
        return _load(fh)["swarms"]


def get(name: str) -> dict[str, Any] | None:
    return list_all().get(name)


def add(name: str, **fields: Any) -> dict[str, Any]:
    """Insert a new swarm. Fails if name already exists."""
    with _locked() as fh:
        data = _load(fh)
        if name in data["swarms"]:
            raise ValueError(f"swarm {name!r} already exists")
        entry = {
            "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            **fields,
        }
        data["swarms"][name] = entry
        _save(fh, data)
        return entry


def update(name: str, **fields: Any) -> dict[str, Any]:
    """Patch fields on an existing swarm. Fails if missing."""
    with _locked() as fh:
        data = _load(fh)
        if name not in data["swarms"]:
            raise KeyError(name)
        data["swarms"][name].update(fields)
        _save(fh, data)
        return data["swarms"][name]


def remove(name: str) -> dict[str, Any]:
    with _locked() as fh:
        data = _load(fh)
        entry = data["swarms"].pop(name, None)
        if entry is None:
            raise KeyError(name)
        _save(fh, data)
        return entry


def used_ports() -> set[int]:
    return {
        int(s["port"]) for s in list_all().values() if isinstance(s.get("port"), int)
    }
