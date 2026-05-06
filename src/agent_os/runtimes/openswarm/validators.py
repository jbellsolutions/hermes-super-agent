"""Validation gate for the build flow.

A validator runs AFTER customization, BEFORE the swarm is registered as
"live" (skill written, available to the router). Failure causes builder.py
to roll the build back atomically.

Three validators ship:

- ``noop``   — accept anything. Only safe in tests.
- ``health`` — boot the swarm via fleet.start, hit the health endpoint, stop.
                 Catches "customization broke server.py" without doing real work.
- ``smoke``  — boot, send a canned prompt via fleet.run, assert non-empty
                 response. Catches "customization broke the agency wiring" but
                 burns a real LLM call.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from . import fleet, http_client


@dataclass
class ValidationResult:
    success: bool
    summary: str = ""
    error: str | None = None
    details: dict[str, Any] | None = None


class Validator(Protocol):
    name: str

    def validate(self, *, name: str, port: int, swarm_dir: Path) -> ValidationResult: ...


class NoopValidator:
    name = "noop"

    def validate(self, *, name: str, port: int, swarm_dir: Path) -> ValidationResult:
        return ValidationResult(success=True, summary="noop validator — skipped")


class HealthValidator:
    """Boot the swarm and hit the health endpoint. No LLM call."""

    name = "health"

    def validate(self, *, name: str, port: int, swarm_dir: Path) -> ValidationResult:
        try:
            fleet.start(name)
        except Exception as e:  # noqa: BLE001
            return ValidationResult(
                success=False,
                error=f"start failed: {type(e).__name__}: {e}",
            )
        try:
            ok = http_client.health(port, timeout=5.0)
        finally:
            try:
                fleet.stop(name)
            except Exception:  # noqa: BLE001
                pass
        if not ok:
            return ValidationResult(
                success=False,
                error="health endpoint did not respond",
            )
        return ValidationResult(success=True, summary="server booted + health OK")


class SmokeValidator:
    """Boot + send a canned prompt + assert non-empty response. Real LLM call."""

    name = "smoke"
    DEFAULT_PROMPT = "Briefly describe what you can produce. One sentence."

    def __init__(self, prompt: str | None = None, agent: str = "auto") -> None:
        self.prompt = prompt or self.DEFAULT_PROMPT
        self.agent = agent

    def validate(self, *, name: str, port: int, swarm_dir: Path) -> ValidationResult:
        try:
            fleet.start(name)
        except Exception as e:  # noqa: BLE001
            return ValidationResult(
                success=False,
                error=f"start failed: {type(e).__name__}: {e}",
            )
        try:
            response = fleet.run(swarm=name, agent=self.agent, prompt=self.prompt)
        except Exception as e:  # noqa: BLE001
            return ValidationResult(
                success=False,
                error=f"smoke prompt failed: {type(e).__name__}: {e}",
            )
        finally:
            try:
                fleet.stop(name)
            except Exception:  # noqa: BLE001
                pass
        text = str(response.get("response", "") or "")
        if not text.strip():
            return ValidationResult(success=False, error="smoke response was empty")
        return ValidationResult(
            success=True,
            summary="smoke passed",
            details={"response_chars": len(text)},
        )


def get_validator(spec: str | Validator | None) -> Validator:
    if spec is None or spec == "noop":
        return NoopValidator()
    if isinstance(spec, str):
        if spec == "health":
            return HealthValidator()
        if spec == "smoke":
            return SmokeValidator()
        raise ValueError(f"unknown validator: {spec!r}")
    if hasattr(spec, "validate"):
        return spec
    raise TypeError(f"can't coerce {spec!r} to a Validator")
