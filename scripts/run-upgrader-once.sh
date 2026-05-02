#!/usr/bin/env bash
# Manually run the nightly upgrader on demand.
set -euo pipefail
uv run python -m agent_os.upgrader.daemon
