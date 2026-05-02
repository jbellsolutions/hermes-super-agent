"""Slack adapter — extends Hermes' built-in Slack with file-upload-to-vault."""
from agent_os.channels.slack.handler import on_file_upload, on_message

__all__ = ["on_message", "on_file_upload"]
