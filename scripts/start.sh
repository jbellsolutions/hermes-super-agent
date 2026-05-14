#!/usr/bin/env bash
# Super Agent start-up: installs Hermes, wires the profile, locks in the
# identity + model, starts the gateway.
# Safe to run on cold deploys (Railway, VPS, fresh Mac). Idempotent.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"

# ── 0. Load the repo .env into the environment ───────────────────────────────
# Railway/Docker inject env vars directly; a fresh `bash scripts/start.sh` on a
# VPS/Mac relies on the repo .env. Load it WITHOUT clobbering anything already
# in the environment (real env wins). `source` chokes on values with spaces, so
# parse by hand.
if [[ -f "$REPO_ROOT/.env" ]]; then
  while IFS='=' read -r _k _v; do
    [[ "$_k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [[ -z "${!_k:-}" ]]; then
      export "$_k=$_v"
    fi
  done < "$REPO_ROOT/.env"
  echo "[start] loaded repo .env"
fi

# Resolve the profile AFTER loading .env so HERMES_PROFILE from .env is honored.
PROFILE="${HERMES_PROFILE:-supersan}"

# ── 1. Tier selection ────────────────────────────────────────────────────────
MODE="${INSTALL_MODE:-}"
if [[ -z "$MODE" ]]; then
  if [[ -t 0 ]]; then
    echo "[start] Pick your power level:"
    echo "  [1] Saiyan       — planner + 14 runtimes, no new infra (~3 min)"
    echo "  [2] Super Saiyan — full Railway fabric + VPS spawning (~30 min)"
    read -r -p "  Choice [2]: " _choice
    [[ "$_choice" == "1" ]] && MODE="saiyan" || MODE="super-saiyan"
  else
    MODE="super-saiyan"
  fi
fi
export INSTALL_MODE="$MODE"
echo "[start] mode: $MODE"

# ── 2. Install Hermes if missing ─────────────────────────────────────────────
if ! command -v hermes >/dev/null 2>&1; then
  echo "[start] installing Hermes..."
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
  # Re-source PATH after install
  export PATH="$HOME/.local/bin:$PATH"
fi

HERMES_VERSION=$(hermes --version 2>/dev/null | head -1 || echo "unknown")
echo "[start] hermes: $HERMES_VERSION | profile: $PROFILE"

# ── 3. Create profile directory ──────────────────────────────────────────────
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
mkdir -p "$PROFILE_DIR"

# ── 4. Inject tier SOUL.md from repo ─────────────────────────────────────────
SOUL_SRC="$REPO_ROOT/SOUL-${MODE}.md"
[[ -f "$SOUL_SRC" ]] || SOUL_SRC="$REPO_ROOT/SOUL.md"
if [[ -f "$SOUL_SRC" ]]; then
  cp "$SOUL_SRC" "$PROFILE_DIR/SOUL.md"
  echo "[start] SOUL.md injected (${MODE})"
fi

# ── 5. Install tier tools ────────────────────────────────────────────────────
if command -v python3 >/dev/null 2>&1 && [[ "$MODE" == "saiyan" ]]; then
  python3 "$REPO_ROOT/install.py" --mode=saiyan --target="$REPO_ROOT" --force 2>/dev/null || true
fi

# ── 6. Sync env vars into profile .env (no-clobber for secrets already set) ──
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
    OPERATOR_NAME|BUSINESS_NAME|BUSINESS_TYPE|INSTALL_MODE|KIMI_K2_*|GLM_MODEL|\
    MIXTRAL_MODEL|LIVEKIT_*|EXA_API_KEY|E2B_API_KEY|RAILWAY_*|DIGITALOCEAN_*)
      [[ -n "$val" ]] && _set_env "$key" "$val"
      ;;
  esac
done < <(env)

echo "[start] profile env synced"

# ── 7. Lock in the Super Agent model config ──────────────────────────────────
# Hermes reads model config from the profile's config.yaml — NOT from the
# HERMES_DEFAULT_MODEL / HERMES_PROVIDER names other tools use. Profile mode
# also ignores the global config, so an unset profile falls back to Hermes'
# built-in default (OpenRouter + Claude). Write the profile config.yaml
# explicitly so a fresh deploy comes up as the real Super Agent.
# Defaults are the locked-in Super Agent stack; override via env if needed.
SA_MODEL="${HERMES_MODEL:-moonshotai/Kimi-K2.6}"
SA_PROVIDER="${HERMES_INFERENCE_PROVIDER:-custom}"
SA_BASE_URL="${HERMES_BASE_URL:-https://api.together.xyz/v1}"
hermes --profile "$PROFILE" config set model.default "$SA_MODEL"     || true
hermes --profile "$PROFILE" config set model.provider "$SA_PROVIDER" || true
hermes --profile "$PROFILE" config set model.base_url "$SA_BASE_URL" || true
# Mirror into the profile .env under the names Hermes actually reads.
_set_env HERMES_MODEL "$SA_MODEL"
_set_env HERMES_INFERENCE_PROVIDER "$SA_PROVIDER"
_set_env HERMES_BASE_URL "$SA_BASE_URL"
echo "[start] model locked: $SA_MODEL via $SA_PROVIDER ($SA_BASE_URL)"

# ── 8. Start gateway ─────────────────────────────────────────────────────────
echo "[start] launching hermes --profile $PROFILE gateway run"
exec hermes --profile "$PROFILE" gateway run
