#!/usr/bin/env bash
set -euo pipefail

echo "# Hermes Super Agent Health Check"
date

echo
printf "Hermes: "
hermes --version 2>/dev/null | head -1 || echo "not available"

echo
printf "Codex: "
codex --version 2>/dev/null || echo "not available"

printf "A0: "
a0 --version 2>/dev/null || echo "not available"

echo
printf "Docker: "
docker --version 2>/dev/null || echo "not available"

printf "Colima: "
if colima status >/dev/null 2>&1; then
  echo "running"
else
  echo "not running"
fi

echo
printf "Agent Zero container: "
if docker ps --filter name=agent-zero --format '{{.Names}} {{.Status}}' 2>/dev/null | grep -q '^agent-zero '; then
  docker ps --filter name=agent-zero --format '{{.Names}} {{.Status}}'
else
  echo "not running"
fi

printf "Agent Zero HTTP: "
if curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:5080 2>/dev/null | grep -q '^200$'; then
  echo "HTTP 200"
else
  echo "not reachable"
fi

printf "A0 launchd: "
if launchctl list | grep -q 'com.justin.a0-connector'; then
  echo "loaded"
else
  echo "not loaded"
fi

printf "A0 tmux session: "
if tmux has-session -t a0 2>/dev/null; then
  echo "running"
else
  echo "not running"
fi

echo
if tmux has-session -t a0 2>/dev/null; then
  echo "A0 footer/status:"
  tmux capture-pane -t a0 -p | tail -8
fi

echo
show_disk() {
  df -h / /Users/home 2>/dev/null || true
}
show_disk
