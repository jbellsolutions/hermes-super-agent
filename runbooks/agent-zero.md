# Runbook: Agent Zero

Agent Zero is the local visual/autonomous agent runtime for Super Agent. It runs as a Docker container and, when paired with A0 Connector, can operate on the host machine's files and shell.

## Known-good local shape

- URL: <http://127.0.0.1:5080>
- Container: `agent-zero`
- Image: `agent0ai/agent-zero:latest`
- Runtime: Colima + Docker CLI on macOS
- Data path: `/Users/home/agent-zero/agent-zero/usr`
- Env path: `/Users/home/agent-zero/agent-zero/usr/.env`
- Host bridge: A0 Connector, tmux session `a0`
- Host Codex wrapper exposed to A0/Agent Zero: `/Users/home/.local/bin/codex`

Keep the UI bound to `127.0.0.1` by default. Use a public/LAN bind only if the deployment intentionally includes auth, firewalling, TLS, and client isolation.

---

## Step-by-step install: what had to happen

These are the exact steps that made Agent Zero work on Justin's Mac. A future Hermes agent should follow this in order instead of guessing.

### 1. Verify host disk before Docker work

Agent Zero's Docker image is large. Failed pulls can corrupt the Colima/Docker metadata store if the host is low on free space.

```bash
df -h / "$HOME"
```

If free space is low, stop and use `runbooks/disk-cleanup.md` first.

### 2. Install the local container runtime

On macOS, use Colima + Docker CLI rather than Docker Desktop unless the operator explicitly wants Docker Desktop.

```bash
brew install docker docker-compose colima
mkdir -p ~/.docker
python3 - <<'PY'
import json, os
p=os.path.expanduser('~/.docker/config.json')
try:
    data=json.load(open(p)) if os.path.exists(p) else {}
except Exception:
    data={}
arr=data.get('cliPluginsExtraDirs') or []
if '/opt/homebrew/lib/docker/cli-plugins' not in arr:
    arr.append('/opt/homebrew/lib/docker/cli-plugins')
data['cliPluginsExtraDirs']=arr
open(p,'w').write(json.dumps(data, indent=2)+'\n')
PY
```

Start Colima with enough disk for image extraction:

```bash
colima start --cpu 4 --memory 6 --root-disk 40 --disk 20 --vm-type vz --mount-type virtiofs
```

If the machine has comfortable free space, this larger profile is better:

```bash
colima start --cpu 4 --memory 8 --disk 80 --vm-type vz --mount-type virtiofs
```

Verify:

```bash
docker version
docker compose version
colima status
```

### 3. Pull and run Agent Zero non-interactively

The Agent Zero website installer works, but for an agent-run setup the deterministic Docker command is easier to audit.

```bash
mkdir -p "$HOME/agent-zero/agent-zero/usr"
docker pull agent0ai/agent-zero:latest

if docker ps -a --format '{{.Names}}' | grep -qx 'agent-zero'; then
  docker rm -f agent-zero
fi

docker run --name agent-zero \
  --label ai.agent0.managed=true \
  --restart unless-stopped \
  -p 127.0.0.1:5080:80 \
  -v "$HOME/agent-zero/agent-zero/usr:/a0/usr" \
  -d agent0ai/agent-zero:latest
```

### 4. Install the model-provider key into Agent Zero

For OpenRouter, Agent Zero expects `API_KEY_OPENROUTER` in its `usr/.env`. Do not print the key in logs, commits, docs, or chat.

```bash
python3 - <<'PY'
from pathlib import Path
import re
src = Path.home()/'.hermes/.env'
dst = Path.home()/'agent-zero/agent-zero/usr/.env'
text = src.read_text()
m = re.search(r'^OPENROUTER_API_KEY=(.+)$', text, re.M)
if not m or not m.group(1).strip():
    raise SystemExit('OPENROUTER_API_KEY not found in ~/.hermes/.env')
key = m.group(1).strip()
dst.parent.mkdir(parents=True, exist_ok=True)
lines = dst.read_text().splitlines() if dst.exists() else []
updated = False
for i, line in enumerate(lines):
    if re.match(r'^\s*(API_KEY_OPENROUTER|OPENROUTER_API_KEY)\s*=', line):
        lines[i] = 'API_KEY_OPENROUTER=' + key
        updated = True
if not updated:
    lines += ['', 'API_KEY_OPENROUTER=' + key]
dst.write_text('\n'.join(lines).rstrip() + '\n')
print('Agent Zero OpenRouter API key installed into usr/.env; value hidden.')
PY

docker restart agent-zero
```

For other providers, use Agent Zero's `API_KEY_<PROVIDER>` convention where supported, for example `API_KEY_OPENAI` or `API_KEY_ANTHROPIC`.

### 5. Verify the web UI is alive

```bash
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:5080 >/tmp/agent-zero-health.html 2>/tmp/agent-zero-curl.err; then
    echo "READY http://127.0.0.1:5080"
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "NOT_READY"
    cat /tmp/agent-zero-curl.err || true
    docker logs --tail 80 agent-zero || true
    exit 1
  fi
done

docker ps --filter name=agent-zero --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Expected HTTP smoke:

```bash
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:5080
# HTTP 200
```

### 6. Verify model key from the UI

Open <http://127.0.0.1:5080>, create a new chat, and ask:

```text
Say "Agent Zero is ready" and nothing else.
```

Expected: Agent Zero returns the exact sentence. If it asks for an API key, the provider key did not load or the selected provider/preset is not using the configured key. Re-check `/Users/home/agent-zero/agent-zero/usr/.env` and restart the container.

### 7. Add A0 Connector for host access

Agent Zero alone is useful as a local web UI. A0 Connector is what made it operational against the host Mac and Codex. Follow `runbooks/a0-connector.md` immediately after Agent Zero is healthy.

### 8. Verify Agent Zero → A0 → host Codex

From Agent Zero, ask it to use `code_execution_remote` and run:

```bash
pwd && command -v codex && codex --version
```

Known-good result on Justin's Mac:

```text
/Users/home
/Users/home/.local/bin/codex
codex-cli 0.125.0
```

For non-interactive Codex calls through A0, redirect stdin so Codex does not hang waiting for extra input:

```bash
codex exec -s read-only --output-last-message /tmp/last.txt 'Reply exactly: READY' </dev/null >/tmp/codex.log 2>&1
cat /tmp/last.txt
```

---

## Daily operations

```bash
# Runtime
colima status
colima start
colima stop

# Agent Zero
docker ps --filter name=agent-zero
docker logs --tail 100 agent-zero
docker restart agent-zero
docker stop agent-zero
docker start agent-zero

# Data directory
open "$HOME/agent-zero/agent-zero/usr"
```

---

## Common fixes

### UI does not load

```bash
docker ps --filter name=agent-zero
docker restart agent-zero
docker logs --tail 120 agent-zero
```

If Docker itself is down:

```bash
colima start
docker start agent-zero
```

### Docker pull failed with I/O or disk errors

Symptoms:

- `failed to extract layer ... input/output error`
- `write ... meta.db: input/output error`
- `No space left on device`

Recovery:

```bash
df -h / "$HOME"
docker system df || true
colima stop || true
colima delete -f || true
limactl disk unlock colima || true
rm -f ~/.colima/_lima/_disks/colima/datadisk
```

Then free disk if needed, restart Colima with a larger disk, and rerun the pull.

### Docker Compose plugin not found

Ensure `~/.docker/config.json` includes:

```json
{
  "cliPluginsExtraDirs": ["/opt/homebrew/lib/docker/cli-plugins"]
}
```

### Agent Zero cannot access the host Mac

Check `runbooks/a0-connector.md` and verify the A0 TUI footer shows:

```text
F3 Read&Write
F4 Code-exec ON
```

---

## Commercial deployment note

For a sellable Super Agent, treat Agent Zero as an optional visual/autonomous runtime, not the core orchestrator. The product should default to Hermes for orchestration and use Agent Zero only when the customer needs a visible agent workspace, profile/plugin experimentation, or host-computer bridging.
