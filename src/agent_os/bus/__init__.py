"""NATS JetStream bus — real-time fleet event pub/sub.

Subject hierarchy:
  agents.{id}.heartbeat       every 30s from each agent
  agents.{id}.task.started    task begins
  agents.{id}.task.completed  task ends with result
  agents.{id}.alert           needs_human | cost_exceeded | error
  fleet.commands.{id}         Admiral → agent directives
"""
from agent_os.bus.nats_publisher import Publisher, publish_event
from agent_os.bus.nats_subscriber import Subscriber

__all__ = ["Publisher", "Subscriber", "publish_event"]
