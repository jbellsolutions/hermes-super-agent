"""Common runtime adapter contract."""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

VAULT_RUNS = Path(os.environ.get("VAULT_ROOT", "./vault")).resolve() / "runs"


@dataclass
class RuntimeResult:
    runtime: str
    job_id: str
    status: str
    output: Any = None
    error: str | None = None
    cost_usd: float = 0.0
    latency_ms: int = 0
    assertions: dict[str, bool] = field(default_factory=dict)


def write_run_artifact(result: RuntimeResult) -> Path:
    out_dir = VAULT_RUNS / result.runtime
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    path = out_dir / f"{ts}-{result.job_id[:8]}.yaml"
    path.write_text(yaml.safe_dump(asdict(result), sort_keys=False))
    return path


def new_job_id() -> str:
    return uuid.uuid4().hex
