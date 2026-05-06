"""Phase B: builder, customizers, validators, upgrade flow.

A synthetic vendor tree (no real OpenSwarm clone) keeps tests fast and
deterministic. The validator/customizer protocols are exercised end-to-end
through the builder; HTTP and subprocess interactions are mocked.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def synthetic_vendor(tmp_path: Path) -> Path:
    """A minimal OpenSwarm-shaped vendor tree."""
    vendor = tmp_path / "vendor-openswarm"
    vendor.mkdir()
    (vendor / "swarm.py").write_text("# fake swarm.py\n")
    (vendor / "server.py").write_text("# fake server.py\n")
    (vendor / "AGENTS.md").write_text("# AGENTS.md\nFake customization guide.\n")
    (vendor / ".env.example").write_text("OPENAI_API_KEY=replace-me\n")
    (vendor / "shared_instructions.md").write_text("# shared\n")
    for agent in ("orchestrator", "deep_research", "docs_agent", "data_analyst_agent"):
        folder = vendor / agent
        folder.mkdir()
        (folder / "instructions.md").write_text(f"# {agent}\n")
    return vendor


@pytest.fixture
def isolated(tmp_path: Path, synthetic_vendor: Path,
             monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    monkeypatch.setenv("OPENSWARM_REGISTRY", str(tmp_path / "registry.yaml"))
    monkeypatch.setenv("OPENSWARM_HOME", str(tmp_path / "swarms"))
    monkeypatch.setenv("VAULT_ROOT", str(tmp_path / "vault"))
    monkeypatch.setenv("OPENSWARM_VENDOR_ROOT", str(synthetic_vendor))
    monkeypatch.setenv("OPENSWARM_PORT_LOW", "9200")
    monkeypatch.setenv("OPENSWARM_PORT_HIGH", "9209")
    import importlib

    from agent_os.runtimes import _base as runtime_base
    from agent_os.runtimes.openswarm import (
        builder,
        customizers,
        fleet,
        invoke,
        ports,
        registry,
        skills,
        validators,
    )
    importlib.reload(runtime_base)
    importlib.reload(registry)
    importlib.reload(ports)
    importlib.reload(skills)
    importlib.reload(fleet)
    importlib.reload(customizers)
    importlib.reload(validators)
    importlib.reload(builder)
    importlib.reload(invoke)
    return {
        "vendor": synthetic_vendor,
        "registry": tmp_path / "registry.yaml",
        "swarms": tmp_path / "swarms",
        "vault": tmp_path / "vault",
    }


# ============================================================
# customizers
# ============================================================

def test_noop_customizer_passes_through(isolated):
    from agent_os.runtimes.openswarm.customizers import (
        BuildContext,
        NoopCustomizer,
    )
    ctx = BuildContext(name="x", description="y", swarm_dir=isolated["vendor"], agents_md="")
    out = NoopCustomizer().customize(ctx)
    assert out.success
    assert out.agents == []


def test_manual_customizer_writes_shared_context(isolated, tmp_path):
    from agent_os.runtimes.openswarm.customizers import (
        BuildContext,
        ManualCustomizer,
    )
    swarm_dir = tmp_path / "manual-clone"
    import shutil
    shutil.copytree(isolated["vendor"], swarm_dir)
    spec = {
        "agents": [{"name": "deep_research", "role": "SEO research",
                    "instructions_append": "FOCUS ON SEO."}],
        "output_types": ["blog_post_md"],
        "examples": ["Write 3 SEO blog posts."],
    }
    cust = ManualCustomizer(spec)
    out = cust.customize(BuildContext(
        name="seo-swarm", description="SEO research and writing",
        swarm_dir=swarm_dir, agents_md="",
    ))
    assert out.success
    assert out.output_types == ["blog_post_md"]
    shared = (swarm_dir / "shared_instructions.md").read_text()
    assert "agent-os: customization" in shared
    assert "SEO research and writing" in shared
    instr = (swarm_dir / "deep_research" / "instructions.md").read_text()
    assert "FOCUS ON SEO." in instr


def test_manual_customizer_idempotent(isolated, tmp_path):
    from agent_os.runtimes.openswarm.customizers import (
        BuildContext,
        ManualCustomizer,
    )
    swarm_dir = tmp_path / "idem-clone"
    import shutil
    shutil.copytree(isolated["vendor"], swarm_dir)
    cust = ManualCustomizer({"shared_context": "one\n"})
    ctx = BuildContext(name="z", description="d",
                       swarm_dir=swarm_dir, agents_md="")
    cust.customize(ctx)
    cust2 = ManualCustomizer({"shared_context": "two\n"})
    cust2.customize(ctx)
    shared = (swarm_dir / "shared_instructions.md").read_text()
    assert shared.count("agent-os: customization") == 1
    assert "two" in shared
    assert "one" not in shared


def test_manual_customizer_skips_missing_agent(isolated, tmp_path):
    from agent_os.runtimes.openswarm.customizers import (
        BuildContext,
        ManualCustomizer,
    )
    swarm_dir = tmp_path / "skip-clone"
    import shutil
    shutil.copytree(isolated["vendor"], swarm_dir)
    out = ManualCustomizer({"agents": [{"name": "nope", "instructions_append": "x"}]}).customize(
        BuildContext(name="z", description="d", swarm_dir=swarm_dir, agents_md="")
    )
    assert out.success
    assert out.agents == []  # missing agent silently skipped


def test_claude_code_customizer_missing_cli(isolated, tmp_path, monkeypatch):
    from agent_os.runtimes.openswarm.customizers import (
        BuildContext,
        ClaudeCodeCustomizer,
    )
    monkeypatch.setattr("shutil.which", lambda _: None)
    out = ClaudeCodeCustomizer().customize(
        BuildContext(name="x", description="y",
                     swarm_dir=isolated["vendor"], agents_md="")
    )
    assert not out.success
    assert "claude CLI not found" in out.error


def test_get_customizer_factory(isolated):
    from agent_os.runtimes.openswarm.customizers import (
        ClaudeCodeCustomizer,
        ManualCustomizer,
        NoopCustomizer,
        get_customizer,
    )
    assert isinstance(get_customizer(None), NoopCustomizer)
    assert isinstance(get_customizer("noop"), NoopCustomizer)
    assert isinstance(get_customizer("manual"), ManualCustomizer)
    assert isinstance(get_customizer("claude_code"), ClaudeCodeCustomizer)
    assert isinstance(get_customizer({"agents": []}), ManualCustomizer)
    with pytest.raises(ValueError):
        get_customizer("nonsense")
    with pytest.raises(TypeError):
        get_customizer(42)  # type: ignore[arg-type]


# ============================================================
# validators
# ============================================================

def test_noop_validator_always_succeeds(isolated, tmp_path):
    from agent_os.runtimes.openswarm.validators import NoopValidator
    res = NoopValidator().validate(name="x", port=1234, swarm_dir=tmp_path)
    assert res.success


def test_health_validator_calls_fleet_and_health(isolated, tmp_path):
    from agent_os.runtimes.openswarm.validators import HealthValidator
    with patch("agent_os.runtimes.openswarm.validators.fleet.start") as start, \
         patch("agent_os.runtimes.openswarm.validators.fleet.stop") as stop, \
         patch("agent_os.runtimes.openswarm.validators.http_client.health",
               return_value=True) as health:
        res = HealthValidator().validate(name="x", port=4242, swarm_dir=tmp_path)
    assert res.success
    start.assert_called_once_with("x")
    stop.assert_called_once_with("x")
    health.assert_called_once_with(4242, timeout=5.0)


def test_health_validator_fails_when_health_false(isolated, tmp_path):
    from agent_os.runtimes.openswarm.validators import HealthValidator
    with patch("agent_os.runtimes.openswarm.validators.fleet.start"), \
         patch("agent_os.runtimes.openswarm.validators.fleet.stop"), \
         patch("agent_os.runtimes.openswarm.validators.http_client.health",
               return_value=False):
        res = HealthValidator().validate(name="x", port=4242, swarm_dir=tmp_path)
    assert not res.success
    assert "health endpoint" in res.error


def test_health_validator_fails_when_start_raises(isolated, tmp_path):
    from agent_os.runtimes.openswarm.validators import HealthValidator
    with patch("agent_os.runtimes.openswarm.validators.fleet.start",
               side_effect=RuntimeError("port stuck")):
        res = HealthValidator().validate(name="x", port=4242, swarm_dir=tmp_path)
    assert not res.success
    assert "start failed" in res.error


def test_get_validator_factory(isolated):
    from agent_os.runtimes.openswarm.validators import (
        HealthValidator,
        NoopValidator,
        SmokeValidator,
        get_validator,
    )
    assert isinstance(get_validator(None), NoopValidator)
    assert isinstance(get_validator("noop"), NoopValidator)
    assert isinstance(get_validator("health"), HealthValidator)
    assert isinstance(get_validator("smoke"), SmokeValidator)
    with pytest.raises(ValueError):
        get_validator("nonsense")


# ============================================================
# builder — happy paths
# ============================================================

def test_build_with_noop_customizer_and_noop_validator(isolated):
    from agent_os.runtimes.openswarm import builder, registry

    out = builder.build(
        "demo-swarm",
        "general demo deliverables",
        customizer="noop",
        validator="noop",
    )
    assert out["name"] == "demo-swarm"
    assert 9200 <= out["port"] <= 9209
    assert Path(out["swarm_dir"]).exists()
    assert (Path(out["swarm_dir"]) / "swarm.py").exists()  # vendor copied
    assert (Path(out["swarm_dir"]) / ".env").exists()      # env_example copied
    assert Path(out["manifest_path"]).exists()
    assert Path(out["skill_path"]).exists()
    assert registry.get("demo-swarm") is not None


def test_build_with_manual_customizer(isolated):
    from agent_os.runtimes.openswarm import builder, registry

    out = builder.build(
        "seo-swarm",
        "SEO research, competitor analysis, blog writing",
        customizer="manual",
        customizer_options={
            "agents": [{
                "name": "deep_research",
                "role": "SEO keyword + competitor research",
                "instructions_append": "Always start with Google Search Console.",
            }],
            "output_types": ["blog_post_md"],
            "examples": ["Write 3 SEO posts on X."],
        },
        validator="noop",
    )
    swarm_dir = Path(out["swarm_dir"])
    shared = (swarm_dir / "shared_instructions.md").read_text()
    assert "SEO research" in shared
    instr = (swarm_dir / "deep_research" / "instructions.md").read_text()
    assert "Google Search Console" in instr
    entry = registry.get("seo-swarm")
    assert entry["customizer"] == "manual"
    assert entry["output_types"] == ["blog_post_md"]
    skill_text = Path(out["skill_path"]).read_text()
    assert "name: seo-swarm-swarm" in skill_text
    assert "SEO research" in skill_text
    assert "blog_post_md" in skill_text


def test_build_with_health_validator(isolated):
    from agent_os.runtimes.openswarm import builder, registry

    with patch("agent_os.runtimes.openswarm.validators.fleet.start"), \
         patch("agent_os.runtimes.openswarm.validators.fleet.stop"), \
         patch("agent_os.runtimes.openswarm.validators.http_client.health",
               return_value=True):
        out = builder.build(
            "health-swarm",
            "general",
            customizer="noop",
            validator="health",
        )
    assert registry.get("health-swarm") is not None
    assert out["validator"] == "health"


def test_per_swarm_manifest_has_correct_shape(isolated):
    import yaml

    from agent_os.runtimes.openswarm import builder
    out = builder.build(
        "shape-swarm", "make decks",
        customizer="noop", validator="noop",
    )
    manifest = yaml.safe_load(Path(out["manifest_path"]).read_text())
    assert manifest["component"] == "swarm.shape-swarm"
    assert manifest["type"] == "vertical-app"
    assert manifest["parent_runtime"] == "runtime.openswarm"
    assert manifest["business_purpose"] == "make decks"
    assert manifest["upstream_signals"] == ["runtime.openswarm"]


# ============================================================
# builder — rollback paths
# ============================================================

def test_build_rejects_reserved_name(isolated):
    from agent_os.runtimes.openswarm import builder
    with pytest.raises(ValueError, match="reserved"):
        builder.build("default", "x", customizer="noop", validator="noop")


def test_build_rejects_invalid_name(isolated):
    from agent_os.runtimes.openswarm import builder
    with pytest.raises(ValueError, match="invalid"):
        builder.build("bad/name", "x", customizer="noop", validator="noop")


def test_build_rejects_duplicate(isolated):
    from agent_os.runtimes.openswarm import builder
    builder.build("dup-swarm", "x", customizer="noop", validator="noop")
    with pytest.raises(ValueError, match="already exists"):
        builder.build("dup-swarm", "x", customizer="noop", validator="noop")


def test_build_rolls_back_on_customizer_failure(isolated):
    from agent_os.runtimes.openswarm import builder, fleet, registry, skills

    class BoomCustomizer:
        name = "boom"

        def customize(self, ctx):
            from agent_os.runtimes.openswarm.customizers import CustomizationOutcome
            return CustomizationOutcome(success=False, error="kaboom")

    with pytest.raises(RuntimeError, match="customization failed"):
        builder.build("boom-swarm", "x", customizer=BoomCustomizer(),
                      validator="noop")

    assert registry.get("boom-swarm") is None
    assert not fleet.folder_for("boom-swarm").exists()
    archive = fleet.ARCHIVE_HOME / "build-failed"
    assert archive.exists() and any(archive.iterdir())
    assert not (isolated["vault"] / "skills" / "active" / "boom-swarm-swarm.md").exists()
    assert not (isolated["vault"] / "skills" / "active" / "boom-swarm.md").exists()
    skills.remove_for("boom-swarm")  # idempotent — would already be gone


def test_build_rolls_back_on_validator_failure(isolated):
    from agent_os.runtimes.openswarm import builder, fleet, registry

    class FailValidator:
        name = "fail"

        def validate(self, *, name, port, swarm_dir):
            from agent_os.runtimes.openswarm.validators import ValidationResult
            return ValidationResult(success=False, error="nope")

    with pytest.raises(RuntimeError, match="validation failed"):
        builder.build("vbad-swarm", "x", customizer="noop",
                      validator=FailValidator())
    assert registry.get("vbad-swarm") is None
    assert not fleet.folder_for("vbad-swarm").exists()


def test_build_rolls_back_when_folder_collision(isolated):
    from agent_os.runtimes.openswarm import builder, fleet
    fleet.folder_for("collide").mkdir(parents=True)
    with pytest.raises(FileExistsError):
        builder.build("collide", "x", customizer="noop", validator="noop")


# ============================================================
# upgrade
# ============================================================

def test_upgrade_no_change_when_sha_matches(isolated):
    from agent_os.runtimes.openswarm import builder, registry
    builder.build("up-swarm", "x", customizer="noop", validator="noop")
    # Force a deterministic sha so "no upgrade" path triggers reliably.
    registry.update("up-swarm", forked_from_sha="abc123")
    with patch("agent_os.runtimes.openswarm.builder._vendor_sha",
               return_value="abc123"):
        out = builder.upgrade("up-swarm", validator="noop")
    assert out["status"] == "no-upgrade"
    assert out["head"] == "abc123"


def test_upgrade_replays_and_swaps(isolated):
    from agent_os.runtimes.openswarm import builder, fleet, registry
    builder.build("swap-swarm", "x", customizer="noop", validator="noop")
    folder = fleet.folder_for("swap-swarm")
    (folder / "marker-old").write_text("old")
    registry.update("swap-swarm", forked_from_sha="OLD")
    # New vendor sha → upgrade should proceed.
    with patch("agent_os.runtimes.openswarm.builder._vendor_sha",
               return_value="NEW"):
        out = builder.upgrade("swap-swarm", validator="noop")
    assert out["status"] == "upgraded"
    assert out["from"] == "OLD"
    assert out["to"] == "NEW"
    # old marker should be archived, not present in live folder
    assert not (folder / "marker-old").exists()
    # archive lives under fleet.ARCHIVE_HOME / "replaced/"
    archive = fleet.ARCHIVE_HOME / "replaced"
    assert any(archive.iterdir())


def test_upgrade_rejects_default(isolated):
    from agent_os.runtimes.openswarm import builder, registry
    registry.add("default", port=9200, agency="open-swarm",
                 forked_from_sha="X", customizer="noop")
    with pytest.raises(ValueError, match="default swarm"):
        builder.upgrade("default")


def test_upgrade_rejects_unknown(isolated):
    from agent_os.runtimes.openswarm import builder
    with pytest.raises(KeyError):
        builder.upgrade("ghost")


# ============================================================
# invoke dispatcher (build + upgrade)
# ============================================================

def test_invoke_build_happy_path(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    result = inv.invoke({
        "op": "build",
        "name": "inv-swarm",
        "description": "build via dispatcher",
        "customizer": "noop",
        "validator": "noop",
    })
    assert result.status == "ok"
    assert result.output["name"] == "inv-swarm"


def test_invoke_build_missing_required_returns_error(isolated):
    from agent_os.runtimes.openswarm import invoke as inv
    result = inv.invoke({"op": "build"})
    assert result.status == "error"
    assert "name" in result.error.lower() or "keyerror" in result.error.lower()


def test_invoke_upgrade_no_change(isolated):
    from agent_os.runtimes.openswarm import builder, registry
    from agent_os.runtimes.openswarm import invoke as inv
    builder.build("up2", "x", customizer="noop", validator="noop")
    registry.update("up2", forked_from_sha="abc")
    with patch("agent_os.runtimes.openswarm.builder._vendor_sha",
               return_value="abc"):
        result = inv.invoke({"op": "upgrade", "swarm": "up2"})
    assert result.status == "ok"
    assert result.output["status"] == "no-upgrade"


# ============================================================
# skill description derivation
# ============================================================

def test_derive_description_with_examples():
    from agent_os.runtimes.openswarm import skills
    desc = skills.derive_description(
        "SEO research and blog writing",
        ["Write 3 SEO posts about AI agents."],
    )
    assert "Use when the user asks about" in desc
    assert "SEO research" in desc
    assert "Example:" in desc


def test_derive_description_no_examples():
    from agent_os.runtimes.openswarm import skills
    desc = skills.derive_description("anything goes here.", [])
    assert "Use when the user asks about" in desc
    assert "Example:" not in desc
