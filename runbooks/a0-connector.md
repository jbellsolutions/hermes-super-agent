# Runbook: A0 Connector

A0 Connector lets the Dockerized Agent Zero instance operate against the host Mac filesystem and shell. This is the bridge that made Agent Zero materially useful in the local Super Agent stack.

## Known-good local setup

- tmux session: `a0`
- launchd label: `com.justin.a0-connector`
- script: `/Users/home/bin/start-a0-connector.sh`
- plist: `/Users/home/Library/LaunchAgents/com.justin.a0-connector.plist`
- Agent Zero host: `http://127.0.0.1:5080`
- A0 working directory / exposed host root: `/Users/home`
- Desired TUI footer: `F3 Read&Write`, `F4 Code-exec ON`

---

## Step-by-step install: what had to happen

### 1. Confirm Agent Zero is running first

```bash
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:5080
```

Expected:

```text
HTTP 200
```

### 2. Install the A0 CLI

Use the official installer:

```bash
curl -LsSf https://cli.agent-zero.ai/install.sh | sh
```

Alternative explicit install used when the installer needs to be reproduced:

```bash
uv tool install --python 3.11 --managed-python --upgrade 'a0 @ https://github.com/agent0ai/a0-connector/archive/refs/tags/v1.5.zip'
```

Verify:

```bash
export PATH="$HOME/.local/bin:$(uv tool dir --bin):$PATH"
command -v a0
a0 --help
a0 --version
```

Known-good version: `1.5`.

### 3. Run A0 in tmux for manual verification

```bash
tmux kill-session -t a0 2>/dev/null || true
export PATH="$HOME/.local/bin:$(uv tool dir --bin):$PATH"
tmux new-session -d -s a0 -x 160 -y 50 -c "$HOME" \
  "PATH=$HOME/.local/bin:$(uv tool dir --bin):$PATH AGENT_ZERO_HOST=http://127.0.0.1:5080 a0 --host http://127.0.0.1:5080"
sleep 5
tmux send-keys -t a0 F3   # Read&Write
tmux send-keys -t a0 F4   # Code-exec ON
tmux capture-pane -t a0 -p | tail -40
```

The important part is the footer. It must show:

```text
F3 Read&Write
F4 Code-exec ON
```

If it shows `Read-only`, press F3. If it shows `Code-exec OFF`, press F4.

### 4. Persist A0 with launchd

Create a wrapper that ensures the tmux session exists and re-enables Read&Write/code execution on startup.

```bash
mkdir -p "$HOME/bin" "$HOME/Library/LaunchAgents"
cat > "$HOME/bin/start-a0-connector.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$(uv tool dir --bin 2>/dev/null || true):/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
SESSION="a0"
HOST="http://127.0.0.1:5080"
cd "$HOME"
while true; do
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -x 160 -y 50 -c "$HOME" "AGENT_ZERO_HOST=$HOST a0 --host $HOST"
    sleep 5
    tmux send-keys -t "$SESSION" F3 || true
    sleep 1
    tmux send-keys -t "$SESSION" F4 || true
  fi
  sleep 60
done
EOF
chmod +x "$HOME/bin/start-a0-connector.sh"
```

Install a LaunchAgent plist. Use `com.justin.a0-connector` on Justin's Mac; use a customer-specific label elsewhere.

```bash
cat > "$HOME/Library/LaunchAgents/com.justin.a0-connector.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.justin.a0-connector</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/home/bin/start-a0-connector.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/Users/home/Library/Logs/a0-connector.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/home/Library/Logs/a0-connector.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$HOME/Library/LaunchAgents/com.justin.a0-connector.plist" 2>/dev/null || true
launchctl load "$HOME/Library/LaunchAgents/com.justin.a0-connector.plist"
```

Verify persistence:

```bash
launchctl list | grep com.justin.a0-connector
tmux has-session -t a0 && echo 'a0 session is running'
tmux capture-pane -t a0 -p | tail -40
```

### 5. Expose Codex to Agent Zero through A0

A0 sessions need a stable `codex` binary on their PATH. On Justin's Mac the real Codex binary is:

```text
/Users/home/.nvm/versions/node/v22.19.0/bin/codex
```

Create a host wrapper:

```bash
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/codex" <<'EOF'
#!/usr/bin/env bash
exec /Users/home/.nvm/versions/node/v22.19.0/bin/codex "$@"
EOF
chmod +x "$HOME/.local/bin/codex"
```

For a different host, replace the path with `command -v codex` from that machine.

### 6. Verify from Agent Zero

From Agent Zero, ask it to use `code_execution_remote` and run:

```bash
pwd && command -v codex && codex --version
```

Known-good result:

```text
/Users/home
/Users/home/.local/bin/codex
codex-cli 0.125.0
```

### 7. Avoid Codex stdin hangs over A0

Interactive CLIs may see A0's remote execution channel as open stdin and wait forever. Use `/dev/null` and output files:

```bash
codex exec -s read-only --output-last-message /tmp/last.txt 'Reply exactly: READY' </dev/null >/tmp/codex.log 2>&1
cat /tmp/last.txt
```

---

## Inspect and control

```bash
# Inspect
tmux capture-pane -t a0 -p | tail -80
launchctl list | grep com.justin.a0-connector

# Attach manually
tmux attach -t a0

# Restart connector
tmux kill-session -t a0
launchctl unload ~/Library/LaunchAgents/com.justin.a0-connector.plist
launchctl load ~/Library/LaunchAgents/com.justin.a0-connector.plist

# Logs
tail -100 ~/Library/Logs/a0-connector.log
tail -100 ~/Library/Logs/a0-connector.err.log
```

---

## Security notes

- A0 with Read&Write + code execution is powerful. Treat it like local shell access.
- Do not expose Agent Zero or A0 directly to the public internet.
- For commercial deployments, isolate each customer/workspace in its own VPS/container boundary and store customer secrets separately.
- Prefer read-only mode when demoing unless the workflow explicitly needs write/code execution.
