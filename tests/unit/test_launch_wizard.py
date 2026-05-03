import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCH_PATH = ROOT / "scripts" / "launch.py"


def load_launch_module():
    spec = importlib.util.spec_from_file_location("launch_wizard", LAUNCH_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hermes_preflight_installs_official_hermes_when_missing(monkeypatch):
    launch = load_launch_module()
    calls = []

    def fake_which(command):
        return None

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

        class Result:
            returncode = 0
            stdout = "Hermes Agent v0.test"
            stderr = ""

        if command == ["bash", "-lc", "hermes --version"] and len(calls) == 1:
            Result.returncode = 127
            Result.stdout = ""
        return Result()

    monkeypatch.setattr(launch.shutil, "which", fake_which)
    monkeypatch.setattr(launch.subprocess, "run", fake_run)

    assert launch.step_hermes_preflight(skip_install=False) is True

    assert any(
        call[0]
        == [
            "bash",
            "-lc",
            "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/"
            "install.sh | bash",
        ]
        for call in calls
    )


def test_hermes_preflight_skips_installer_when_hermes_exists(monkeypatch):
    launch = load_launch_module()
    calls = []

    monkeypatch.setattr(launch.shutil, "which", lambda command: "/usr/local/bin/hermes")

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))

        class Result:
            returncode = 0
            stdout = "Hermes Agent v0.test"
            stderr = ""

        return Result()

    monkeypatch.setattr(launch.subprocess, "run", fake_run)

    assert launch.step_hermes_preflight(skip_install=False) is True
    assert all("install.sh" not in " ".join(call[0]) for call in calls)
    assert calls[0][0] == ["hermes", "--version"]
