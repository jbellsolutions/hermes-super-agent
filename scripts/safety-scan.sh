#!/usr/bin/env bash
# safety-scan.sh — fail if any tracked file contains a known leak pattern.
#
# Same regex set used in the 2026-05-08 security cleanup. Add new patterns
# below the SCAN_PATTERNS marker when you onboard a new service / customer /
# infrastructure target you don't want in the public repo.
#
# Usage:
#   ./scripts/safety-scan.sh                # scan working tree
#   ./scripts/safety-scan.sh --staged       # scan only staged changes
#   ./scripts/safety-scan.sh --history      # scan all of git history (slow)
#
# Exits 0 = clean, 1 = leak found.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-tree}"

# === SCAN_PATTERNS — edit this block when you need to scrub a new identifier ===
PATTERNS=(
    # API key prefixes
    'sk-ant-[a-zA-Z0-9_-]{30,}'
    'sk-proj-[a-zA-Z0-9_-]{30,}'
    'ghp_[a-zA-Z0-9]{36}'
    'github_pat_[a-zA-Z0-9_]{60,}'
    'xox[bpoasr]-[a-zA-Z0-9-]{10,}'
    'AIza[a-zA-Z0-9_-]{30,}'
    'AKIA[A-Z0-9]{16}'
    'dop_v1_[a-f0-9]{40,}'
    # Private keys
    'BEGIN (RSA |OPENSSH |DSA |EC |PGP )?PRIVATE KEY'
    # Internal identifiers — see SECURITY.md if you need to add to this list
    'jbellsolutions@gmail\.com'
    # DigitalOcean IPs from the 2026-05 cleanup. Generalize the pattern, not
    # individual IPs, so future leaks are caught too.
    '\b138\.197\.43\.196\b'
    '\b157\.230\.83\.196\b'
    '\b157\.230\.95\.186\b'
    '\b134\.122\.17\.43\b'
    '\b142\.93\.54\.26\b'
    '\b167\.172\.131\.251\b'
    '\b142\.93\.64\.250\b'
    '\b104\.236\.11\.200\b'
    # Internal infrastructure / customer-tagged project names
    '\bpaperclip-server\b'
    '\bpaperclip-ops\b'
    '\bagentstack-hermes\b'
    '\bhermes-worker\b'
    '\bhermes-scheduler\b'
    '\bskool-group-engagement\b'
    '\bengerlina\b'
    '\bai-integrators\b'
)
# === end SCAN_PATTERNS ===

# Files this script always ignores (their content is allowed to mention the
# patterns above for legitimate reasons — e.g. this scanner itself).
ALLOWLIST_RE='^(scripts/safety-scan\.sh|\.gitignore|docs/working-with-this-repo\.md)$'

RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; BOLD="\033[1m"; RESET="\033[0m"

found=0

scan_blob () {
    local pat="$1"
    local matches
    if [ "$MODE" = "--staged" ]; then
        matches=$(git diff --cached --unified=0 | grep -nE "^\+.*$pat" || true)
    elif [ "$MODE" = "--history" ]; then
        matches=$(git log --all -p 2>/dev/null | grep -E "$pat" | head -5 || true)
    else
        # working tree (default)
        matches=$(git ls-files | grep -Ev "$ALLOWLIST_RE" | xargs grep -lE "$pat" 2>/dev/null || true)
    fi
    if [ -n "$matches" ]; then
        echo -e "${RED}✗ pattern matched: ${BOLD}$pat${RESET}"
        echo "$matches" | head -5 | sed 's/^/    /'
        found=$((found + 1))
    fi
}

echo "Hermes safety-scan — mode: $MODE"
echo

for pat in "${PATTERNS[@]}"; do
    scan_blob "$pat"
done

echo
if [ "$found" -eq 0 ]; then
    echo -e "${GREEN}✓ clean${RESET} — $((${#PATTERNS[@]})) patterns checked, no matches."
    exit 0
else
    echo -e "${RED}✗ $found pattern(s) matched. Resolve before publishing to the public repo.${RESET}"
    echo
    echo -e "${YELLOW}Tip:${RESET} run ${BOLD}git diff${RESET} or ${BOLD}git diff --cached${RESET} to see what changed."
    echo -e "${YELLOW}Tip:${RESET} if a pattern is a false positive (e.g. it's in the safety-scan.sh itself),"
    echo "      add the file to ALLOWLIST_RE in this script."
    exit 1
fi
