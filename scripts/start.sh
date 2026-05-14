#!/usr/bin/env bash
# SuperSAN agent start-up: installs Hermes, wires the supersan profile, starts the gateway.
# Safe to run on cold deploys (Railway, VPS, fresh Mac). Idempotent.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE="${HERMES_PROFILE:-supersan}"
export PATH="$HOME/.local/bin:$PATH"

# ── 1. Install Hermes if missing ──────────────────────────────────────────────
if ! command -v hermes >/dev/null 2>&1; then
  echo "[start] installing Hermes..."
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
  # Re-source PATH after install
  export PATH="$HOME/.local/bin:$PATH"
fi

HERMES_VERSION=$(hermes --version 2>/dev/null | head -1 || echo "unknown")
echo "[start] hermes: $HERMES_VERSION | profile: $PROFILE"

# ── 2. Create profile directory ───────────────────────────────────────────────
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
mkdir -p "$PROFILE_DIR"

# ── 3. Inject SOUL.md from repo ───────────────────────────────────────────────
SOUL_SRC="$REPO_ROOT/SOUL.md"
if [[ -f "$SOUL_SRC" ]]; then
  cp "$SOUL_SRC" "$PROFILE_DIR/SOUL.md"
  echo "[start] SOUL.md injected from repo"
fi

# ── 4. Sync env vars into profile .env (no-clobber for secrets already set) ──
PROFILE_ENV="$PROFILE_DIR/.env"
touch "$PROFILE_ENV"

_set_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$PROFILE_ENV" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$PROFILE_ENV"
  else
    echo "${key}=${val}" >> "$PROFILE_ENV"
  fi
}

# Sync all relevant env vars from the process environment into the profile
while IFS='=' read -r key val; do
  case "$key" in
    HERMES_*|OPENAI_*|ANTHROPIC_*|TOGETHER_*|TELEGRAM_*|NOTION_*|SUPABASE_*|\
    OPERATOR_NAME|BUSINESS_NAME|BUSINESS_TYPE|KIMI_K2_*|GLM_MODEL|MIXTRAL_MODEL|\
    LIVEKIT_*|EXA_API_KEY|E2B_API_KEY|RAILWAY_*|DIGITALOCEAN_*)
      [[ -n "$val" ]] && _set_env "$key" "$val"
      ;;
  esac
done < <(env)

echo "[start] profile env synced"

# ── 5. Start gateway ──────────────────────────────────────────────────────────
echo "[start] launching hermes --profile $PROFILE gateway run"
exec hermes --profile "$PROFILE" gateway run
