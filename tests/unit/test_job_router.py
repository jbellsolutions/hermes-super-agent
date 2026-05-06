"""Job routing rules — the load-bearing piece of the orchestrator."""
from agent_os.orchestrator.adapters.job_router import Job, route


def test_default_to_hermes():
    assert route(Job(prompt="be helpful")) == "hermes_self"


def test_coding_interactive_to_claude_subagents():
    assert route(Job(prompt="add test", tags={"coding", "interactive"})) == "claude_subagents"


def test_coding_background_to_codex():
    assert route(Job(prompt="implement X", tags={"coding", "background"})) == "codex_cli"


def test_coding_aider():
    assert route(Job(prompt="rename Y", tags={"coding", "aider"})) == "aider"


def test_browser_structured_to_browser_use():
    assert route(Job(prompt="extract", tags={"browser", "structured"})) == "browser_use"


def test_visual_autonomous_ui_to_agent_zero():
    assert route(Job(prompt="drive visual task", tags={"visual", "autonomous-ui"})) == "agent_zero"


def test_agent_zero_tag_to_agent_zero():
    assert route(Job(prompt="open the local UI", tags={"agent-zero"})) == "agent_zero"


def test_autonomous_grind_to_openclaw():
    assert route(Job(prompt="grind", tags={"autonomous-grind"})) == "openclaw"


def test_long_running_to_managed():
    assert route(Job(prompt="long", tags={"long-running"})) == "claude_managed"


def test_estimated_minutes_long_running():
    assert route(Job(prompt="long", estimated_minutes=120)) == "claude_managed"


def test_sandboxed_code_to_e2b():
    assert route(Job(prompt="run", tags={"sandboxed-code"})) == "e2b"


def test_search_to_exa():
    assert route(Job(prompt="find", tags={"search", "articles"})) == "exa"


def test_voice_to_livekit():
    assert route(Job(prompt="say", tags={"voice"})) == "livekit"


def test_terminal():
    assert route(Job(prompt="cron", tags={"cron"})) == "terminal"


def test_build_swarm_to_openswarm():
    assert route(Job(prompt="build me an SEO swarm", tags={"build-swarm"})) == "openswarm"


def test_multi_deliverable_to_openswarm():
    assert route(
        Job(prompt="investor pitch", tags={"multi-deliverable"})
    ) == "openswarm"


def test_investor_pitch_to_openswarm():
    assert route(Job(prompt="pitch", tags={"investor-pitch"})) == "openswarm"


def test_swarm_tag_to_openswarm():
    assert route(Job(prompt="run swarm", tags={"swarm"})) == "openswarm"


def test_openswarm_beats_coding_when_both_present():
    # build-swarm should win over coding tags so the agent-builder runs
    assert route(
        Job(prompt="build a coding swarm", tags={"build-swarm", "coding", "interactive"})
    ) == "openswarm"
