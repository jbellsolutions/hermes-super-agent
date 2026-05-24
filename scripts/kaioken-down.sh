#!/usr/bin/env bash
# kaioken-down.sh — stop the local Hermes fabric.
#
# Usage:
#   ./scripts/kaioken-down.sh              # stop containers, keep volumes
#   ./scripts/kaioken-down.sh --purge      # also remove volumes (vault, db)
#   ./scripts/kaioken-down.sh --kill-spawns  # also kill any hermes-superagent-* containers
#
# By default `down` only stops the compose services. Spawned superagents
# (hermes-superagent-<id>-<task>) were created OUTSIDE compose via the
# Docker API, so they linger unless --kill-spawns is passed.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; RESET="\033[0m"

PURGE=""
KILL_SPAWNS=""
for arg in "$@"; do
    case "$arg" in
        --purge) PURGE=1 ;;
        --kill-spawns) KILL_SPAWNS=1 ;;
        --help|-h)
            sed -n '2,10p' "$0"
            exit 0
            ;;
        *) echo "unknown arg: $arg"; exit 2 ;;
    esac
done

COMPOSE_FILES=(-f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.kaioken.yml)

echo -e "${B}Kaioken — shutdown${RESET}"
echo

# Kill spawned superagent containers first (they're not managed by compose).
if [ -n "$KILL_SPAWNS" ]; then
    spawns=$(docker ps -a --filter "label=hermes.role=superagent" --format '{{.Names}}' 2>/dev/null || true)
    if [ -n "$spawns" ]; then
        echo "==> Stopping spawned superagents"
        for c in $spawns; do
            echo "  removing $c"
            docker rm -f "$c" >/dev/null 2>&1 || true
        done
    else
        echo "  no spawned superagents found"
    fi
    echo
fi

echo "==> Stopping compose services"
if [ -n "$PURGE" ]; then
    docker compose "${COMPOSE_FILES[@]}" down -v
    echo -e "${G}✓ stopped and volumes purged${RESET}"
else
    docker compose "${COMPOSE_FILES[@]}" down
    echo -e "${G}✓ stopped (volumes preserved — use --purge to wipe)${RESET}"
fi
echo

# Report leftover spawns the user might want to clean up.
remaining=$(docker ps -a --filter "label=hermes.role=superagent" --format '{{.Names}}' 2>/dev/null || true)
if [ -n "$remaining" ]; then
    echo -e "${Y}⚠ leftover spawned superagents:${RESET}"
    echo "$remaining" | sed 's/^/    /'
    echo "    Remove with: ./scripts/kaioken-down.sh --kill-spawns"
fi
