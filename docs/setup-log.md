# Setup Log

## 2026-05-01 — Initial super-agent stack build

### Agent Zero

- Installed Docker CLI, Docker Compose, and Colima via Homebrew.
- Started Colima with Docker runtime.
- Pulled `agent0ai/agent-zero:latest`.
- Started Agent Zero container:

```bash
docker run --name agent-zero \
  --label ai.agent0.managed=true \
  --restart unless-stopped \
  -p 127.0.0.1:5080:80 \
  -v "$HOME/agent-zero/agent-zero/usr:/a0/usr" \
  -d agent0ai/agent-zero:latest
```

- Verified Agent Zero UI at `http://127.0.0.1:5080`.
- Configured Agent Zero with OpenRouter key via `/Users/home/agent-zero/agent-zero/usr/.env`.
- Verified chat response: `Agent Zero is ready`.

### Disk cleanup

- Cleared caches/logs/package-manager temp files.
- Removed downloaded/local video files from Desktop, Downloads, Documents, Movies.
- Deleted local Time Machine APFS snapshot that was holding deleted space.
- Free space improved from roughly 11 GiB to roughly 23 GiB.

### Codex

- Verified Codex CLI installed and authenticated.
- Version: `codex-cli 0.125.0`.
- Smoke test in temp git repo returned `CODEX_READY`.

### A0 CLI Connector

- Installed A0 CLI connector v1.5:

```bash
uv tool install --python 3.11 --managed-python --upgrade 'a0 @ https://github.com/agent0ai/a0-connector/archive/refs/tags/v1.5.zip'
```

- Started A0 in tmux session `a0` pointed at Agent Zero.
- Set local access to Read&Write.
- Enabled remote code execution.
- Created launchd service `com.justin.a0-connector` to keep A0 running.
- Exposed Codex to Agent Zero/A0 at `/Users/home/.local/bin/codex`.
- Verified from Agent Zero through A0:

```text
/Users/home
/Users/home/.local/bin/codex
codex-cli 0.125.0
```

### Documentation repo

- Created local repo: `/Users/home/Desktop/Hermes Super Agent`.
- Added docs/runbooks/templates/scripts structure.
