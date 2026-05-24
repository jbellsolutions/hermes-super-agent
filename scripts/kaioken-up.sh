#!/usr/bin/env bash
# kaioken-up.sh — bring up the full local Hermes fabric in Docker.
#
# This is Kaioken's one-command installer. Equivalent to:
#   docker compose -f deploy/compose/docker-compose.yml \
#                  -f deploy/compose/docker-compose.kaioken.yml up -d
# …with friendlier output and a doctor check first.
#
# Usage:
#   ./scripts/kaioken-up.sh              # standard bring-up
#   ./scripts/kaioken-up.sh --telegram   # also start the Telegram bot
#   ./scripts/kaioken-up.sh --follow     # tail admiral logs after start
#   ./scripts/kaioken-up.sh --rebuild    # force docker compose build --no-cache
#
# Exit codes:
#   0  fabric is up and healthy
#   1  docker not running / install failed
#   2  unhealthy service after timeout

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; D="\033[2m"; RESET="\033[0m"

FOLLOW=""
TELEGRAM=""
REBUILD=""
for arg in "$@"; do
    case "$arg" in
        --follow|-f) FOLLOW=1 ;;
        --telegram) TELEGRAM=1 ;;
        --rebuild) REBUILD=1 ;;
        --help|-h)
            sed -n '2,18p' "$0"
            exit 0
            ;;
        *) echo "unknown arg: $arg"; exit 2 ;;
    esac
done

echo -e "${B}⚡ Kaioken — local Hermes fabric${RESET}"
echo

# --- Doctor: Docker available + enough RAM/disk ---
echo "==> Doctor"
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${R}✗ docker not found on PATH${RESET}"
    echo "  Install Docker Desktop: https://docs.docker.com/desktop/"
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    echo -e "${R}✗ docker daemon not running${RESET}"
    echo "  Start Docker Desktop (or your daemon) and re-run."
    exit 1
fi
echo "  docker:    $(docker --version | head -1)"

# Free RAM (best-effort across mac + linux).
if command -v vm_stat >/dev/null 2>&1; then
    # macOS: page size * free pages → MB
    page_size=$(vm_stat | head -1 | awk '{print $8}' | tr -d '.')
    free_pages=$(vm_stat | awk '/Pages free/ {print $3}' | tr -d '.')
    if [ -n "$page_size" ] && [ -n "$free_pages" ]; then
        free_mb=$(( page_size * free_pages / 1024 / 1024 ))
        echo "  free RAM:  ~${free_mb}MB"
        if [ "$free_mb" -lt 2048 ]; then
            echo -e "  ${Y}⚠ under 2GB free — Kaioken needs ~800MB just for the fabric${RESET}"
        fi
    fi
elif [ -r /proc/meminfo ]; then
    free_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    free_mb=$(( free_kb / 1024 ))
    echo "  free RAM:  ~${free_mb}MB"
fi

# Free disk in repo root.
free_disk=$(df -h "$REPO_ROOT" | awk 'NR==2 {print $4}')
echo "  free disk: ${free_disk}"

# .env present and at least has ANTHROPIC_API_KEY?
if [ ! -f "$REPO_ROOT/.env" ]; then
    echo -e "  ${Y}⚠ no .env file — copying from .env.example${RESET}"
    if [ -f "$REPO_ROOT/.env.example" ]; then
        cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
        echo -e "    ${Y}edit .env and add at minimum ANTHROPIC_API_KEY, then re-run${RESET}"
        exit 1
    else
        echo -e "  ${R}✗ .env.example also missing — repo is incomplete${RESET}"
        exit 1
    fi
fi
if ! grep -q "^ANTHROPIC_API_KEY=sk-" "$REPO_ROOT/.env" 2>/dev/null; then
    echo -e "  ${Y}⚠ ANTHROPIC_API_KEY in .env doesn't look set (or doesn't start with sk-)${RESET}"
    echo "    Admiral will boot but LLM-backed runtimes won't work."
fi
echo

# --- Compose up ---
COMPOSE_FILES=(-f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.kaioken.yml)
PROFILES=()
if [ -n "$TELEGRAM" ]; then
    echo -e "  ${Y}⚠ --telegram is a no-op in this release — the agent_os.channels.telegram_bot${RESET}"
    echo -e "  ${Y}  module isn't packaged yet. Run the bot on the host pointed at admiral:8080.${RESET}"
    echo
fi

if [ -n "$REBUILD" ]; then
    echo "==> Rebuilding images (--rebuild)"
    docker compose "${COMPOSE_FILES[@]}" build --no-cache
    echo
fi

echo "==> Starting fabric"
docker compose "${COMPOSE_FILES[@]}" "${PROFILES[@]}" up -d
echo

# --- Wait for healthchecks ---
echo "==> Waiting for services to become healthy (up to 90s)"
deadline=$(( $(date +%s) + 90 ))
services=(hermes-nats hermes-temporal hermes-coordinator hermes-admiral)
while true; do
    all_up=1
    for svc in "${services[@]}"; do
        # `docker inspect -f '{{.State.Health.Status}}'` returns 'healthy',
        # 'unhealthy', 'starting', or empty if no healthcheck.
        status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$svc" 2>/dev/null || echo "missing")
        case "$status" in
            healthy|running) : ;;
            *) all_up=0; break ;;
        esac
    done
    if [ "$all_up" -eq 1 ]; then
        break
    fi
    if [ "$(date +%s)" -ge "$deadline" ]; then
        echo -e "${Y}⚠ timeout waiting for healthchecks. Current state:${RESET}"
        for svc in "${services[@]}"; do
            status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$svc" 2>/dev/null || echo "missing")
            echo "  $svc: $status"
        done
        echo
        echo "  Inspect logs:  docker compose ${COMPOSE_FILES[*]} logs"
        exit 2
    fi
    sleep 2
done

echo -e "${G}✓ fabric healthy${RESET}"
echo
echo "  Admiral A2A:    http://localhost:8080/agentCard"
echo "  Temporal UI:    http://localhost:8088"
echo "  NATS monitor:   http://localhost:8222"
echo
echo "  Try a spawn:  uv run python examples/kaioken_spawn_demo.py"
echo "  Tear down:    ./scripts/kaioken-down.sh"
echo

if [ -n "$FOLLOW" ]; then
    echo "==> Tailing Admiral logs (Ctrl-C to stop, fabric keeps running)"
    docker compose "${COMPOSE_FILES[@]}" logs -f admiral
fi
