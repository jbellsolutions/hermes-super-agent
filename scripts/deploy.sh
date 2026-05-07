#!/usr/bin/env bash
# deploy.sh — one-command Railway deploy of the Hermes fabric.
#
# Brings up: NATS → Temporal → Coordinator → Archon → Admiral
# Wires service URLs across them automatically.
# Reads credentials from .env (run scripts/setup.sh first).
#
# Idempotent — re-run any time. Existing services are updated, not recreated.
#
# Usage:
#   ./scripts/deploy.sh                # deploy everything
#   ./scripts/deploy.sh --skip-archon  # skip optional services
#
# Requires: railway CLI (auto-installed on macOS via brew if missing).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

B="\033[1m"; G="\033[32m"; Y="\033[33m"; C="\033[36m"; D="\033[2m"; R="\033[0m"

# ---------- args ----------
SKIP_ARCHON=false
SKIP_ADMIRAL=false
for arg in "$@"; do
    case "$arg" in
        --skip-archon)  SKIP_ARCHON=true ;;
        --skip-admiral) SKIP_ADMIRAL=true ;;
    esac
done

# ---------- preflight ----------
echo
echo -e "${B}Hermes Fabric — Railway deploy${R}"
echo

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${Y}No .env at repo root.${R} Run ${C}./scripts/setup.sh${R} first."
    exit 1
fi

# Source .env so we can use values for env-var commands.
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

# Install railway CLI if missing
if ! command -v railway &>/dev/null; then
    echo -e "${Y}railway CLI not found.${R}"
    if command -v brew &>/dev/null; then
        echo "Installing via Homebrew..."
        brew install railway
    else
        echo "Install from: https://docs.railway.com/guides/cli"
        exit 1
    fi
fi

# Login check
if ! railway whoami &>/dev/null; then
    echo "Not logged in. Running railway login..."
    railway login
fi

# Project link check
if [ ! -f "$REPO_ROOT/.railway/config.json" ] && [ ! -f "$REPO_ROOT/railway.toml" ]; then
    echo
    echo -e "${C}First-time setup: linking this repo to a Railway project.${R}"
    cd "$REPO_ROOT"
    railway init
fi

cd "$REPO_ROOT"

# ---------- helpers ----------

# Check if a railway service exists
service_exists() {
    railway service "$1" --json 2>/dev/null | grep -q '"id"' || return 1
}

# Add a service if it doesn't exist
add_service() {
    local name="$1"
    if service_exists "$name"; then
        echo -e "  ${D}service '$name' already exists — reusing${R}"
    else
        echo -e "  ${G}+ adding service '$name'${R}"
        railway add --service "$name" --no-interactive >/dev/null 2>&1 || railway add --service "$name"
    fi
}

# Set env vars on a service from a list of KEY=VALUE pairs (only sets non-empty)
set_vars() {
    local service="$1"; shift
    local pairs=()
    for kv in "$@"; do
        local key="${kv%%=*}" val="${kv#*=}"
        # Only set if value is non-empty
        if [ -n "$val" ]; then
            pairs+=("$key=$val")
        fi
    done
    if [ ${#pairs[@]} -gt 0 ]; then
        railway variables --service "$service" --set "${pairs[@]}" >/dev/null
        echo -e "  ${D}set ${#pairs[@]} env vars${R}"
    fi
}

# Deploy a service from a sub-directory
deploy() {
    local name="$1" path="$2"
    echo -e "${B}→ deploying $name${R}  ${D}(from $path)${R}"
    add_service "$name"
    railway up --service "$name" --path "$path" --detach >/dev/null
    echo -e "  ${G}✓ build started${R}"
}

# Get the public domain of a service
get_domain() {
    local name="$1"
    railway domain --service "$name" --json 2>/dev/null \
        | grep -o '"[^"]*\.up\.railway\.app"' | head -1 | tr -d '"' || true
}

# Generate a public domain if the service doesn't have one
ensure_domain() {
    local name="$1"
    local domain; domain="$(get_domain "$name")"
    if [ -z "$domain" ]; then
        railway domain --service "$name" >/dev/null 2>&1 || true
        domain="$(get_domain "$name")"
    fi
    echo "$domain"
}

# ---------- 1. NATS ----------
echo
echo -e "${B}━━━ 1/5  NATS (event bus) ━━━${R}"
deploy nats deploy/nats
NATS_DOMAIN="$(ensure_domain nats)"
NATS_URL_FOR_FABRIC="nats://${NATS_DOMAIN}:4222"
echo -e "  ${G}NATS_URL${R} = $NATS_URL_FOR_FABRIC"

# ---------- 2. Temporal ----------
echo
echo -e "${B}━━━ 2/5  Temporal (durable workflows) ━━━${R}"
deploy temporal deploy/temporal
TEMPORAL_DOMAIN="$(ensure_domain temporal)"
TEMPORAL_HOST_FOR_FABRIC="${TEMPORAL_DOMAIN}:7233"
echo -e "  ${G}TEMPORAL_HOST${R} = $TEMPORAL_HOST_FOR_FABRIC"

# ---------- 3. Coordinator ----------
echo
echo -e "${B}━━━ 3/5  Coordinator (fan-out engine) ━━━${R}"
deploy coordinator deploy/coordinator
set_vars coordinator \
    "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}" \
    "OPENAI_API_KEY=${OPENAI_API_KEY:-}" \
    "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}" \
    "MOONSHOT_API_KEY=${MOONSHOT_API_KEY:-}" \
    "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
    "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}" \
    "NATS_URL=$NATS_URL_FOR_FABRIC" \
    "COORDINATOR_DEFAULT_MODEL=${COORDINATOR_DEFAULT_MODEL:-claude-sonnet-4-5}" \
    "COORDINATOR_MAX_CONCURRENCY=${COORDINATOR_MAX_CONCURRENCY:-50}"
COORD_DOMAIN="$(ensure_domain coordinator)"
COORDINATOR_URL_FOR_FABRIC="https://${COORD_DOMAIN}"
echo -e "  ${G}COORDINATOR_URL${R} = $COORDINATOR_URL_FOR_FABRIC"

# ---------- 4. Archon (optional) ----------
ARCHON_URL_FOR_FABRIC=""
if [ "$SKIP_ARCHON" = "false" ]; then
    echo
    echo -e "${B}━━━ 4/5  Archon agent builder (optional, stub mode) ━━━${R}"
    deploy archon deploy/archon
    ARCHON_DOMAIN="$(ensure_domain archon)"
    ARCHON_URL_FOR_FABRIC="https://${ARCHON_DOMAIN}"
    echo -e "  ${G}ARCHON_A2A_URL${R} = $ARCHON_URL_FOR_FABRIC"
fi

# ---------- 5. Admiral ----------
if [ "$SKIP_ADMIRAL" = "false" ]; then
    echo
    echo -e "${B}━━━ 5/5  Admiral (the brain) ━━━${R}"
    deploy admiral .
    set_vars admiral \
        "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}" \
        "OPENAI_API_KEY=${OPENAI_API_KEY:-}" \
        "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-}" \
        "MOONSHOT_API_KEY=${MOONSHOT_API_KEY:-}" \
        "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
        "OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}" \
        "NATS_URL=$NATS_URL_FOR_FABRIC" \
        "TEMPORAL_HOST=$TEMPORAL_HOST_FOR_FABRIC" \
        "COORDINATOR_URL=$COORDINATOR_URL_FOR_FABRIC" \
        "COORDINATOR_DEFAULT_MODEL=${COORDINATOR_DEFAULT_MODEL:-claude-sonnet-4-5}" \
        "ARCHON_A2A_URL=$ARCHON_URL_FOR_FABRIC" \
        "RAILWAY_API_KEY=${RAILWAY_API_KEY:-}" \
        "DO_API_TOKEN=${DO_API_TOKEN:-}" \
        "DO_SSH_KEY_FINGERPRINT=${DO_SSH_KEY_FINGERPRINT:-}" \
        "RETELL_API_KEY=${RETELL_API_KEY:-}" \
        "RETELL_AGENT_ID=${RETELL_AGENT_ID:-}" \
        "INSTANTLY_API_KEY=${INSTANTLY_API_KEY:-}" \
        "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}" \
        "TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID:-}" \
        "AGENTOPS_API_KEY=${AGENTOPS_API_KEY:-}"
    ADMIRAL_DOMAIN="$(ensure_domain admiral)"
    echo -e "  ${G}HERMES_BASE_URL${R} = https://${ADMIRAL_DOMAIN}"
fi

# ---------- summary ----------
echo
echo -e "${G}${B}✓ deploy complete${R}"
echo
echo -e "${B}Service URLs:${R}"
echo -e "  ${C}NATS${R}         tcp://${NATS_DOMAIN}:4222"
echo -e "  ${C}Temporal${R}     ${TEMPORAL_DOMAIN}:7233"
echo -e "  ${C}Coordinator${R}  $COORDINATOR_URL_FOR_FABRIC"
[ -n "$ARCHON_URL_FOR_FABRIC" ] && echo -e "  ${C}Archon${R}       $ARCHON_URL_FOR_FABRIC"
[ "$SKIP_ADMIRAL" = "false" ] && echo -e "  ${C}Admiral${R}      https://${ADMIRAL_DOMAIN}"
echo
echo -e "${D}Builds run in the background. Watch progress at:${R}"
echo -e "  ${C}https://railway.app/dashboard${R}"
echo
echo -e "${D}First build takes ~5 min. Subsequent deploys are ~1–2 min.${R}"
echo
