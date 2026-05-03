#!/usr/bin/env bash
# One-shot bootstrap: install uv, sync Python, install pnpm deps, copy .env.example.
set -euo pipefail

if ! command -v uv >/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

uv sync
if command -v pnpm >/dev/null; then
  pnpm install
fi

[[ -f .env ]] || cp .env.example .env

echo "agent-os bootstrap complete. fill in .env, then run: hermes doctor && hermes"
