#!/usr/bin/env bash
# log.sh — append a timestamped entry to WORKLOG.md
#
# Usage:
#   ./scripts/log.sh "tried X, broke on Y"
#   ./scripts/log.sh -                       # opens $EDITOR for a longer entry
#
# WORKLOG.md is gitignored. It never gets pushed anywhere. Back it up
# manually (iCloud, Dropbox, Time Machine) if you want it preserved.
# Or run ./scripts/publish.sh to push the WORKLOG to the private internal
# remote on a separate `worklog` branch.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/WORKLOG.md"

# First time? Write a header.
if [ ! -f "$LOG" ]; then
    cat > "$LOG" <<EOF
# Work Log

Private build/test log. Gitignored — never published. Most-recent entries on top.

EOF
fi

# Build the entry
ts="$(date '+%Y-%m-%d %H:%M')"

if [ "${1:-}" = "-" ] || [ -z "${1:-}" ]; then
    # Multi-line entry via $EDITOR
    tmp="$(mktemp /tmp/worklog.XXXXXX.md)"
    "${EDITOR:-vi}" "$tmp"
    body="$(cat "$tmp")"
    rm -f "$tmp"
    if [ -z "$body" ]; then
        echo "(empty entry — nothing logged)"
        exit 0
    fi
else
    body="$*"
fi

# Build new content: header + new entry + old entries
header="$(sed -n '1,4p' "$LOG")"
old_body="$(sed -n '5,$p' "$LOG")"

{
    echo "$header"
    echo "## $ts"
    echo
    echo "$body"
    echo
    echo "$old_body"
} > "$LOG.tmp"

mv "$LOG.tmp" "$LOG"

echo "✓ logged: $body" | head -c 120
echo
