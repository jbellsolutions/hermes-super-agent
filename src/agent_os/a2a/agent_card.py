"""Agent Card — the self-description JSON that A2A agents expose at GET /agentCard.

The Admiral reads Agent Cards at boot from registered fleet agents to build
its live capability map. External agents read the Admiral's card to discover
what it can receive.

Spec: https://google.github.io/A2A/#/documentation?id=agent-card
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSkill:
    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "examples": self.examples,
        }


@dataclass
class AgentCard:
    name: str
    description: str
    version: str
    url: str                           # base URL where this agent is reachable
    skills: list[AgentSkill] = field(default_factory=list)
    default_input_modes: list[str] = field(default_factory=lambda: ["text/plain"])
    default_output_modes: list[str] = field(default_factory=lambda: ["text/plain"])
    capabilities: dict[str, Any] = field(default_factory=dict)
    authentication: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "url": self.url,
            "defaultInputModes": self.default_input_modes,
            "defaultOutputModes": self.default_output_modes,
            "skills": [s.to_dict() for s in self.skills],
            "capabilities": self.capabilities,
            "authentication": self.authentication,
        }


def build_card(
    agent_id: str | None = None,
    base_url: str | None = None,
    extra_skills: list[AgentSkill] | None = None,
) -> AgentCard:
    """Build the Admiral Hermes Agent Card from environment + catalog.

    HERMES_AGENT_ID  — agent identifier (default: "admiral")
    HERMES_BASE_URL  — public base URL (default: http://localhost:8080)
    """
    _id = agent_id or os.getenv("HERMES_AGENT_ID", "admiral")
    _url = base_url or os.getenv("HERMES_BASE_URL", "http://localhost:8080")

    skills: list[AgentSkill] = [
        AgentSkill(
            id="orchestrate",
            name="Fleet Orchestration",
            description=(
                "Orchestrate multi-agent tasks across the Hermes fleet. "
                "Classifies jobs by tier, routes to specialists, and reports status via NATS."
            ),
            tags=["orchestrate", "multi-agent", "delegation"],
            examples=["Research competitors and produce a slide deck", "Fan out this task to 10 sub-agents"],
        ),
        AgentSkill(
            id="fan-out",
            name="Parallel Fan-Out",
            description="Decompose a job into parallel sub-tasks handled by up to N agents via the deployed Coordinator service.",
            tags=["fan-out", "swarm", "parallel", "coordinator"],
            examples=["Analyze 200 company websites in parallel"],
        ),
        AgentSkill(
            id="spawn-specialist",
            name="Specialist Spawning",
            description="Create and deploy a new Tier 1 specialist agent on Railway via Archon.",
            tags=["build-specialist", "spawn", "archon"],
            examples=["Create a LinkedIn outreach specialist"],
        ),
        AgentSkill(
            id="spawn-superagent",
            name="Superagent Provisioning",
            description="Provision a full Tier 2 superagent on a dedicated VPS with its own sub-fleet.",
            tags=["spawn-superagent", "vps", "fleet"],
            examples=["Spin up a cold email superagent with Kimi coordinator and phone agent"],
        ),
    ]

    if extra_skills:
        skills.extend(extra_skills)

    return AgentCard(
        name=f"Hermes — {_id}",
        description=(
            "Admiral Hermes: multi-agent fleet orchestrator. "
            "Runs tier classification, tool planning, and model routing before every delegation. "
            "Speaks A2A, publishes to NATS JetStream, wraps fan-out in Temporal workflows."
        ),
        version="1.0.0",
        url=_url,
        skills=skills,
        capabilities={
            "streaming": False,
            "pushNotifications": True,  # via NATS
            "stateTransitionHistory": True,
        },
        authentication={"schemes": ["bearer"]},
    )
