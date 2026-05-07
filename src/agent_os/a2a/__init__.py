"""Google A2A Protocol — Universal agent communication layer.

Exposes three HTTP routes that make Admiral Hermes (and any spawned agent)
a first-class A2A citizen:

  GET  /agentCard       → Agent Card JSON (skills, auth, contact endpoint)
  POST /messages        → receive a task delegation from another agent
  GET  /tasks/{task_id} → task status (SUBMITTED → WORKING → COMPLETED/FAILED)

The plan_card output flows into A2A task response bodies so any delegating
agent (or the Admiral itself) sees the same plan cards that go to Telegram.

Spec: google/A2A on GitHub (Linux Foundation, April 2025).
"""
from agent_os.a2a.agent_card import AgentCard, build_card
from agent_os.a2a.server import create_a2a_app, A2ATask, TaskStatus

__all__ = ["AgentCard", "build_card", "create_a2a_app", "A2ATask", "TaskStatus"]
