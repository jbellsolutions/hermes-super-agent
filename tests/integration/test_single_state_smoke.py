"""Single-state guarantee — every channel writes to the same conversation log."""
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_vault(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("VAULT_ROOT", d)
        # reload modules that read VAULT_ROOT at import time
        import importlib

        import agent_os.orchestrator.adapters.vault_memory as vm
        importlib.reload(vm)
        import agent_os.channels.slack.handler as slack_h
        importlib.reload(slack_h)
        import agent_os.channels.telegram.handler as tg_h
        importlib.reload(tg_h)
        import agent_os.channels.web.handler as web_h
        importlib.reload(web_h)
        yield Path(d)


def test_three_channels_write_to_same_conversation(tmp_vault):
    from agent_os.channels.slack.handler import on_message as slack_msg
    from agent_os.channels.telegram.handler import on_message as tg_msg
    from agent_os.channels.web.handler import on_message as web_msg

    slack_msg({"user": "U123", "text": "from slack"})
    tg_msg({"from": {"id": 456}, "text": "from telegram"})
    web_msg("session-1", "from web")

    convo_dir = tmp_vault / "conversations"
    files = list(convo_dir.glob("*.md"))
    assert len(files) == 1, (
        f"expected single canonical conversation file, got {[f.name for f in files]}"
    )
    contents = files[0].read_text()
    assert "from slack" in contents
    assert "from telegram" in contents
    assert "from web" in contents
