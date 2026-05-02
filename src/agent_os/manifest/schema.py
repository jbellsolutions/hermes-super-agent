"""manifest.yaml schema. Every component in the system declares one."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentSpec(BaseModel):
    name: str
    role: str
    tools: list[str] = []
    cost_budget_daily_usd: float | None = None


class OutputSpec(BaseModel):
    type: str
    consumer: str


class Manifest(BaseModel):
    component: str
    type: str  # vertical-app | specialist-runtime | quality-skill | channel | core
    description: str | None = None
    depends_on: dict[str, str] = Field(default_factory=dict)
    agents: list[AgentSpec] = []
    data_sources: list[str] = []
    outputs: list[OutputSpec] = []
    upstream_signals: list[str] = []
    downstream_consumers: list[str] = []


def validate(data: dict[str, Any]) -> Manifest:
    return Manifest.model_validate(data)
