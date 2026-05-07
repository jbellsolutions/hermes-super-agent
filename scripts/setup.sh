#!/usr/bin/env bash
# setup.sh — interactive .env builder for the Hermes fabric.
#
# Walks through every credential the fabric uses, with the URL where to get
# each one. Skips anything you already have. Writes .env at the repo root.
#
# Usage:
#   ./scripts/setup.sh
#
# Idempotent — re-run any time to update keys. Existing values are shown
# (last 4 chars only) and kept on Enter.
set -euo pipefail

# Resolve repo root regardless of where you run from
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

# Colors
B="\033[1m"; G="\033[32m"; Y="\033[33m"; C="\033[36m"; D="\033[2m"; R="\033[0m"

echo
echo -e "${B}Hermes Fabric — interactive setup${R}"
echo -e "${D}Walks you through every credential the fleet needs.${R}"
echo -e "${D}Press Enter to skip / keep existing.${R}"
echo

# Seed .env from .env.example if missing
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${G}Created${R} .env from .env.example"
    else
        touch "$ENV_FILE"
        echo -e "${G}Created${R} empty .env"
    fi
fi

# Read current value of an env var from .env
current() {
    local key="$1"
    grep -E "^$key=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- | sed 's/^"//;s/"$//' || true
}

# Update or append a key=value to .env (atomic, preserves comments)
set_var() {
    local key="$1" val="$2"
    # Quote if value contains spaces or special chars
    if echo "$val" | grep -qE '[[:space:]"#$&|<>]'; then
        val="\"$(echo "$val" | sed 's/"/\\"/g')\""
    fi
    if grep -qE "^$key=" "$ENV_FILE"; then
        # macOS sed quirks: write to tmp then mv
        local tmp="${ENV_FILE}.tmp"
        awk -v k="$key" -v v="$val" '
            BEGIN{set=0}
            $0 ~ "^"k"=" {print k"="v; set=1; next}
            {print}
            END{if (!set) print k"="v}
        ' "$ENV_FILE" > "$tmp" && mv "$tmp" "$ENV_FILE"
    else
        echo "$key=$val" >> "$ENV_FILE"
    fi
}

# Mask a value for display (last 4 chars only)
masked() {
    local v="$1"
    [ -z "$v" ] && { echo "(empty)"; return; }
    [ ${#v} -le 4 ] && { echo "***"; return; }
    echo "***${v: -4}"
}

# Prompt for one variable
ask() {
    local key="$1" label="$2" url="${3:-}" required="${4:-no}"
    local cur; cur="$(current "$key")"
    echo -e "${C}$label${R}  ${D}[${key}]${R}"
    [ -n "$url" ] && echo -e "  ${D}Get one: $url${R}"
    [ -n "$cur" ] && echo -e "  ${D}Current: $(masked "$cur")${R}"
    [ "$required" = "yes" ] && echo -e "  ${Y}Required for the fleet to function.${R}"
    printf "  > "
    read -r val
    if [ -n "$val" ]; then
        set_var "$key" "$val"
        echo -e "  ${G}saved${R}"
    elif [ -z "$cur" ] && [ "$required" = "yes" ]; then
        echo -e "  ${Y}skipped (required — re-run to add later)${R}"
    fi
    echo
}

# =============================================================================
# 1. LLM keys (at least one is required)
# =============================================================================
echo -e "${B}━━━ 1/6  LLM API keys ━━━${R}"
echo -e "${D}You need at least one. Anthropic is the default. Add others if you want${R}"
echo -e "${D}to use them per-job (e.g. cheap fan-outs on DeepSeek).${R}"
echo
ask ANTHROPIC_API_KEY    "Anthropic"          "https://console.anthropic.com/settings/keys"          yes
ask OPENAI_API_KEY       "OpenAI"             "https://platform.openai.com/api-keys"
ask DEEPSEEK_API_KEY     "DeepSeek"           "https://platform.deepseek.com/api_keys"
ask MOONSHOT_API_KEY     "Moonshot (Kimi)"    "https://platform.moonshot.ai"
ask GOOGLE_API_KEY       "Google (Gemini)"    "https://aistudio.google.com/apikey"
ask OPENROUTER_API_KEY   "OpenRouter (catch-all)" "https://openrouter.ai/keys"

# =============================================================================
# 2. Telegram (Admiral interface)
# =============================================================================
echo -e "${B}━━━ 2/6  Telegram bot (your interface to Admiral) ━━━${R}"
echo -e "${D}Talk to @BotFather on Telegram to create a bot, then talk to${R}"
echo -e "${D}@userinfobot to get your chat ID.${R}"
echo
ask TELEGRAM_BOT_TOKEN   "Telegram bot token" "https://t.me/BotFather"          yes
ask TELEGRAM_CHAT_ID     "Your Telegram chat ID" "https://t.me/userinfobot"     yes

# =============================================================================
# 3. DigitalOcean (Tier 2 superagent VPSes)
# =============================================================================
echo -e "${B}━━━ 3/6  DigitalOcean (for spawning superagent VPSes) ━━━${R}"
echo -e "${D}Each Tier 2 superagent gets its own \$4–6/mo droplet.${R}"
echo -e "${D}Skip if you don't plan to spawn Tier 2 superagents yet.${R}"
echo
ask DO_API_TOKEN         "DigitalOcean API token" "https://cloud.digitalocean.com/account/api/tokens"
echo -e "${D}Now upload your laptop's SSH public key to DO and paste the fingerprint:${R}"
echo -e "${D}  doctl compute ssh-key import hermes-fleet --public-key-file ~/.ssh/id_rsa.pub${R}"
echo -e "${D}  doctl compute ssh-key list --format Fingerprint --no-header${R}"
ask DO_SSH_KEY_FINGERPRINT "DO SSH key fingerprint"

# =============================================================================
# 4. Outbound channels (optional — enables COO Specialist)
# =============================================================================
echo -e "${B}━━━ 4/6  Outbound channels (optional) ━━━${R}"
echo -e "${D}Skip these if you don't want phone or cold-email capabilities yet.${R}"
echo
ask RETELL_API_KEY       "Retell AI (phone)"    "https://retellai.com"
ask RETELL_AGENT_ID      "Retell agent ID"
ask INSTANTLY_API_KEY    "Instantly.ai (cold email)" "https://app.instantly.ai/app/settings/integrations"

# =============================================================================
# 5. Spawning
# =============================================================================
echo -e "${B}━━━ 5/6  Tier 1 specialist spawning (optional) ━━━${R}"
echo -e "${D}Archon generates new specialist agents on demand. Skip for now if unsure.${R}"
echo
ask RAILWAY_API_KEY      "Railway API token (for spawning Tier 1 specialists)" "https://railway.app/account/tokens"

# =============================================================================
# 6. Observability (free tier covers most usage)
# =============================================================================
echo -e "${B}━━━ 6/6  Observability ━━━${R}"
echo -e "${D}AgentOps gives you a unified dashboard for cost, latency, and errors.${R}"
echo
ask AGENTOPS_API_KEY     "AgentOps"             "https://app.agentops.ai/settings/projects"

echo
echo -e "${G}${B}✓ setup complete${R}"
echo
echo -e "Saved to ${C}$ENV_FILE${R}"
echo
echo -e "Next:"
echo -e "  ${C}./scripts/deploy.sh${R}    deploys the whole fleet to Railway"
echo
