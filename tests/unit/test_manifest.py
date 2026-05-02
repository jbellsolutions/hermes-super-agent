"""Manifest schema validation."""
from agent_os.manifest.schema import validate


def test_minimal_manifest():
    m = validate({"component": "x", "type": "core"})
    assert m.component == "x"
    assert m.type == "core"


def test_with_outputs():
    m = validate({
        "component": "y",
        "type": "vertical-app",
        "outputs": [{"type": "email", "consumer": "smartlead"}],
    })
    assert len(m.outputs) == 1
    assert m.outputs[0].consumer == "smartlead"


def test_dependencies():
    m = validate(
        {"component": "z", "type": "core", "depends_on": {"agent-os.orchestrator": ">=0.1"}}
    )
    assert "agent-os.orchestrator" in m.depends_on
