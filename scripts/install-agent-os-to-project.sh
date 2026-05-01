#!/usr/bin/env bash
set -euo pipefail

# Install the vendored Builder Methods Agent OS commands/standards into the current project.
# Usage:
#   ./scripts/install-agent-os-to-project.sh /path/to/project [--commands-only]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_OS_DIR="$ROOT_DIR/third_party/agent-os"
PROJECT_DIR="${1:-$PWD}"
shift || true

if [[ ! -d "$AGENT_OS_DIR" ]]; then
  echo "Agent OS vendor dir not found: $AGENT_OS_DIR" >&2
  exit 1
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Upstream uses tac, which is absent on default macOS. If tac is missing but tail exists,
# provide a small PATH shim that maps tac to tail -r for this install invocation.
SHIM_DIR=""
if ! command -v tac >/dev/null 2>&1 && command -v tail >/dev/null 2>&1; then
  SHIM_DIR="$(mktemp -d /tmp/agent-os-shim-XXXXXX)"
  cat > "$SHIM_DIR/tac" <<'SHIM'
#!/usr/bin/env bash
exec tail -r "$@"
SHIM
  chmod +x "$SHIM_DIR/tac"
  export PATH="$SHIM_DIR:$PATH"
fi

bash "$AGENT_OS_DIR/scripts/project-install.sh" "$@"

if [[ -n "$SHIM_DIR" ]]; then
  rm -rf "$SHIM_DIR"
fi
