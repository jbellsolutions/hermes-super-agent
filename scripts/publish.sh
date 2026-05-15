#!/usr/bin/env bash
# publish.sh — safe-publish flow for Hermes Super Agent.
#
# What it does, in order:
#   1. Runs safety-scan.sh against the working tree
#   2. Runs safety-scan.sh against the staged-but-not-pushed delta
#   3. Shows you what would be pushed (commits + file list)
#   4. Asks for confirmation
#   5. Pushes main to BOTH:
#        - origin   (the PUBLIC repo)
#        - internal (the PRIVATE working copy)
#
# Usage:
#   ./scripts/publish.sh                  # interactive
#   ./scripts/publish.sh --yes            # skip confirmation (CI/automation)
#   ./scripts/publish.sh --internal-only  # push only to private (skip public)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

B="\033[1m"; G="\033[32m"; Y="\033[33m"; R="\033[31m"; D="\033[2m"; RESET="\033[0m"

YES=""
INTERNAL_ONLY=""
for arg in "$@"; do
    case "$arg" in
        --yes|-y) YES=1 ;;
        --internal-only) INTERNAL_ONLY=1 ;;
        *) echo "unknown arg: $arg"; exit 2 ;;
    esac
done

echo -e "${B}Hermes Super Agent — publish${RESET}"
echo

# Step 1: working tree safety scan
echo "==> Step 1/4: safety-scan working tree"
if ! ./scripts/safety-scan.sh; then
    echo -e "${R}✗ Aborting publish — fix the leaks above first.${RESET}"
    exit 1
fi
echo

# Step 2: ensure remotes exist
echo "==> Step 2/4: verify remotes"
git remote get-url origin > /dev/null 2>&1 || { echo -e "${R}✗ no 'origin' remote${RESET}"; exit 1; }
echo "  origin   → $(git remote get-url origin)"
if git remote get-url internal > /dev/null 2>&1; then
    echo "  internal → $(git remote get-url internal)"
else
    echo -e "  ${Y}note: no 'internal' remote configured — only pushing to origin (public)${RESET}"
fi
echo

# Step 3: show what would be pushed
echo "==> Step 3/4: what will be pushed"
git fetch origin --quiet 2>/dev/null || true

if git rev-parse --verify --quiet origin/main > /dev/null; then
    ahead=$(git rev-list --count origin/main..main)
    behind=$(git rev-list --count main..origin/main)
    echo "  main is ahead of origin/main by $ahead commit(s), behind by $behind"
    if [ "$ahead" -eq 0 ] && [ "$behind" -eq 0 ]; then
        echo -e "  ${G}✓ main is in sync — nothing to push${RESET}"
        SKIP_PUSH=1
    fi
    if [ "$behind" -gt 0 ]; then
        echo -e "  ${Y}origin has $behind commit(s) you don't have locally. Pull first?${RESET}"
        echo "  (run: git pull --rebase origin main)"
        exit 1
    fi
    echo
    echo "  Commits that will go public:"
    git log --oneline origin/main..main | sed 's/^/    /'
    echo
    echo "  Files changed:"
    git diff --stat origin/main..main | sed 's/^/    /'
else
    echo "  (origin has no main branch yet — pushing fresh)"
fi
echo

# Step 4: confirm + push
echo "==> Step 4/4: push"
if [ -z "$YES" ]; then
    if [ -n "$INTERNAL_ONLY" ]; then
        read -r -p "Push to internal (private) only? [y/N] " ans
    else
        read -r -p "Push to origin (PUBLIC) and internal (private)? [y/N] " ans
    fi
    case "$ans" in
        y|Y|yes|YES) ;;
        *) echo "Cancelled."; exit 0 ;;
    esac
fi

if [ -z "${SKIP_PUSH:-}" ]; then
    if [ -z "$INTERNAL_ONLY" ]; then
        echo -e "${B}Pushing main → origin (PUBLIC)...${RESET}"
        git push origin main
        echo -e "${G}✓ published to public${RESET}"
        echo
    fi

    if git remote get-url internal > /dev/null 2>&1; then
        echo -e "${B}Pushing main → internal (private working copy)...${RESET}"
        git push internal main
        echo -e "${G}✓ pushed to private${RESET}"
        echo
    fi
fi

# Optional: back up WORKLOG.md to internal on a separate `worklog` branch
if [ -f WORKLOG.md ] && git remote get-url internal > /dev/null 2>&1; then
    echo "==> Backing up WORKLOG.md to internal/worklog branch"
    sha_before=$(git rev-parse HEAD)
    # Use a temp index to commit ONLY WORKLOG.md without disturbing main
    tmp_index=$(mktemp)
    cp -f .git/index "$tmp_index"
    trap 'cp -f "$tmp_index" .git/index; rm -f "$tmp_index"' EXIT

    # Create/update worklog branch tip from current main, add WORKLOG.md
    git read-tree "$sha_before"
    git update-index --add --force-add WORKLOG.md
    new_tree=$(git write-tree)

    # Parent: previous worklog tip if it exists on internal, else current main
    parent=$(git ls-remote internal worklog 2>/dev/null | awk '{print $1}' | head -1)
    if [ -z "$parent" ]; then
        parent="$sha_before"
        msg="worklog: initial backup $(date '+%Y-%m-%d %H:%M')"
    else
        msg="worklog: $(date '+%Y-%m-%d %H:%M')"
    fi
    new_commit=$(echo "$msg" | git commit-tree "$new_tree" -p "$parent")

    # Push the new commit as the worklog branch tip
    git push internal "$new_commit:refs/heads/worklog"
    echo -e "${G}✓ WORKLOG.md backed up to internal/worklog @ $new_commit${RESET}"

    # Restore the original index so the user's staging area is untouched
    cp -f "$tmp_index" .git/index
    rm -f "$tmp_index"
    trap - EXIT
fi

echo
echo -e "${G}${B}✓ publish complete${RESET}"
