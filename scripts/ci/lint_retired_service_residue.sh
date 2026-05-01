#!/usr/bin/env bash
# Guard retired service names out of active startup/config/runtime paths.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PATTERN='runtime_orchestrator|runtime-orchestrator|main_runtime_orchestrator|tools_server|tools-server'
TARGETS=(
  ".github"
  "novaic-agent-runtime"
  "novaic-app/scripts"
  "novaic-app/src"
  "novaic-app/src-tauri"
  "novaic-common"
  "scripts"
)

if rg -n "$PATTERN" "${TARGETS[@]}" \
  --glob '!**/.venv/**' \
  --glob '!**/node_modules/**' \
  --glob '!**/target/**' \
  --glob '!scripts/ci/lint_retired_service_residue.sh' \
  --glob '!scripts/ci/lint_current_docs_residue.sh'; then
  echo "Retired service residue found in active paths." >&2
  exit 1
fi

echo "RETIRED_SERVICE_RESIDUE_LINT=PASS"
