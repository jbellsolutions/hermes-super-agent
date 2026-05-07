#!/usr/bin/env bash
# deploy.sh — one-command Railway deploy of the Hermes fabric.
#
# Brings up: NATS → Temporal → Coordinator → (Archon) → Admiral
# Wires service URLs across them automatically.
# Reads credentials from .env (run scripts/setup.sh first).
#
# Idempotent — re-run any time. Existing services are updated, not recreated.
#
# Usage:
#   ./scripts/deploy.sh                # deploy everything
#   ./scripts/deploy.sh --skip-archon  # skip Archon
#   ./scripts/deploy.sh --skip-admiral # skip Admiral
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

# Load .env safely — never execute shell expansions on values that are API keys.
# We parse KEY=VALUE lines, strip optional surrounding quotes, and `export` the
# value as a literal string. Backticks and $(...) in a token will NOT be evaluated.
load_env_safe() {
    local file="$1"
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip comments + blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        # Match KEY=VALUE (key = letters/digits/_)
        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            local k="${BASH_REMATCH[1]}" v="${BASH_REMATCH[2]}"
            # Strip surrounding single or double quotes if present
            if [[ "$v" =~ ^\"(.*)\"$ ]] || [[ "$v" =~ ^\'(.*)\'$ ]]; then
                v="${BASH_REMATCH[1]}"
            fi
            # Trim trailing CR (Windows line endings)
            v="${v%$'\r'}"
            export "$k=$v"
        fi
    done < "$file"
}
load_env_safe "$ENV_FILE"

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

# Login check (opens a browser if not logged in)
if ! railway whoami &>/dev/null; then
    echo -e "${C}Opening browser for Railway login...${R}"
    railway login
fi

# Project link check — prompt to init if not linked
cd "$REPO_ROOT"
if ! railway status --json 2>/dev/null | grep -q '"projectId"'; then
    echo
    echo -e "${C}Creating a new Railway project named 'hermes-fabric'...${R}"
    railway init --name hermes-fabric
fi

# ---------- helpers ----------

# Check if a railway service already exists in this project
service_exists() {
    local name="$1"
    railway service list --json 2>/dev/null \
        | grep -oE "\"name\"[[:space:]]*:[[:space:]]*\"$name\"" >/dev/null
}

# Add a service if it doesn't exist
add_service() {
    local name="$1"
    if service_exists "$name"; then
        echo -e "  ${D}service '$name' already exists — reusing${R}"
    else
        echo -e "  ${G}+ adding service '$name'${R}"
        railway add --service "$name" >/dev/null
    fi
}

# Set env vars on a service. Only forwards keys with non-empty values.
set_vars() {
    local service="$1"; shift
    local pairs=()
    for kv in "$@"; do
        local key="${kv%%=*}" val="${kv#*=}"
        [ -n "$val" ] && pairs+=("$key=$val")
    done
    if [ ${#pairs[@]} -gt 0 ]; then
        # `railway variable set` accepts multiple KEY=VALUE positional args
        railway variable set --service "$service" --skip-deploys "${pairs[@]}" >/dev/null
        echo -e "  ${D}set ${#pairs[@]} env vars${R}"
    fi
}

# Deploy a service from a sub-directory. Path "." means current dir (Admiral).
deploy() {
    local name="$1" path="$2"
    echo -e "${B}→ deploying $name${R}  ${D}(from ${path})${R}"
    add_service "$name"
    if [ "$path" = "." ]; then
        railway up --service "$name" --detach >/dev/null
    else
        # --path-as-root makes the sub-dir the build context root,
        # so Railway finds Dockerfile at deploy/<name>/Dockerfile.
        railway up "$path" --path-as-root --service "$name" --detach >/dev/null
    fi
    echo -e "  ${G}✓ build started${R}"
}

# Generate or fetch a public domain for a service. Returns the domain on stdout.
ensure_domain() {
    local name="$1"
    # `railway domain --service NAME` either prints existing or generates new
    railway domain --service "$name" 2>&1 \
        | grep -oE '[a-zA-Z0-9-]+\.up\.railway\.app' \
        | head -1
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

# ---------- post-deploy health check ----------
# Builds run in the background. Poll /health on the HTTP services until 200
# (or timeout). NATS / Temporal aren't HTTP-checkable on their main ports —
# we skip them here; if Coordinator and Admiral come up green, those work.
echo
echo -e "${B}Waiting for services to come online…${R}"
echo -e "${D}First build takes ~5 min. Polling every 15s.${R}"

wait_for_health() {
    local label="$1" url="$2" timeout="${3:-600}"
    local elapsed=0
    printf "  %-12s " "$label"
    while [ "$elapsed" -lt "$timeout" ]; do
        if curl -sf -o /dev/null --max-time 5 "$url"; then
            echo -e "${G}✓ ready${R}  ${D}($url)${R}"
            return 0
        fi
        sleep 15
        elapsed=$((elapsed + 15))
        printf "."
    done
    echo -e "  ${Y}still building — check Railway dashboard${R}"
    return 1
}

wait_for_health "Coordinator" "${COORDINATOR_URL_FOR_FABRIC}/health" 600 || true
[ "$SKIP_ADMIRAL" = "false" ] && wait_for_health "Admiral" "https://${ADMIRAL_DOMAIN}/health" 600 || true

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
echo -e "${D}Watch logs / restart at: ${C}https://railway.app/dashboard${R}"
echo
