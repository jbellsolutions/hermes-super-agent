#!/usr/bin/env bash
# Rebuild the system graph from manifest.yaml files.
set -euo pipefail
uv run python -m agent_os.manifest.aggregator
