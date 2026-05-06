"""Slack adapter — extends Hermes' built-in Slack with file-upload-to-vault
and OpenSwarm slash commands."""
from agent_os.channels.slack.handler import on_file_upload, on_message
from agent_os.channels.slack.swarm_commands import handle_command as on_slash_command

__all__ = ["on_message", "on_file_upload", "on_slash_command"]
