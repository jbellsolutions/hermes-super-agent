"""All packages must import cleanly. This is the floor."""


def test_orchestrator():
    import agent_os.orchestrator  # noqa: F401
    from agent_os.orchestrator import boot  # noqa: F401
    from agent_os.orchestrator.adapters import job_router, vault_memory  # noqa: F401


def test_runtimes():
    from agent_os.runtimes import _base  # noqa: F401
    from agent_os.runtimes.aider import invoke as aider_invoke  # noqa: F401
    from agent_os.runtimes.browser_use import invoke as browser_invoke  # noqa: F401
    from agent_os.runtimes.claude_managed import invoke as cm_invoke  # noqa: F401
    from agent_os.runtimes.claude_subagents import invoke as cs_invoke  # noqa: F401
    from agent_os.runtimes.codex_cli import invoke as codex_invoke  # noqa: F401
    from agent_os.runtimes.computer_use import invoke as cu_invoke  # noqa: F401
    from agent_os.runtimes.e2b import invoke as e2b_invoke  # noqa: F401
    from agent_os.runtimes.exa import invoke as exa_invoke  # noqa: F401
    from agent_os.runtimes.livekit import invoke as lk_invoke  # noqa: F401
    from agent_os.runtimes.openclaw import invoke as openclaw_invoke  # noqa: F401
    from agent_os.runtimes.terminal import invoke as term_invoke  # noqa: F401


def test_manifest():
    import agent_os.manifest  # noqa: F401
    from agent_os.manifest.aggregator import build_graph  # noqa: F401
    from agent_os.manifest.schema import Manifest, validate  # noqa: F401


def test_quality():
    from agent_os.quality import audit, council, research  # noqa: F401


def test_upgrader():
    import agent_os.upgrader  # noqa: F401
    from agent_os.upgrader.daemon import run_nightly  # noqa: F401
    from agent_os.upgrader.streams import (  # noqa: F401
        agi1,
        aider,
        awesome_hermes,
        browser_use,
        codex,
        hermes,
        mcp_registry,
        nemoclaw,
        openclaw,
        vendor_health,
    )


def test_channels():
    from agent_os.channels.slack import on_message as slack_on_message  # noqa: F401
    from agent_os.channels.telegram import on_message as tg_on_message  # noqa: F401
    from agent_os.channels.voice import voice_session  # noqa: F401
    from agent_os.channels.web import on_message as web_on_message  # noqa: F401


def test_observability():
    from agent_os.observability import trace  # noqa: F401


def test_composio():
    from agent_os.composio import (  # noqa: F401
        call,
        connect,
        discover,
        is_configured,
        list_connections,
    )
