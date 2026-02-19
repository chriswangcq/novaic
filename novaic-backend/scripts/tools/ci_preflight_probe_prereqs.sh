#!/usr/bin/env bash
set -euo pipefail

# Ensures leak probe prerequisites are present on CI/host:
# - lsof
# - pgrep
#
# ============================================================
# HOST DEPENDENCY POLICY (Round 007 Decision, finalized)
# ============================================================
# Policy Choice: Option A — Ubuntu/Debian Linux only.
#
# Rationale: The current CI runner matrix is ubuntu-latest only.
# macOS and Windows runners are NOT supported and are NOT expected.
# If a non-Linux runner is introduced, this script MUST be extended
# before that runner can run the probe.
#
# Non-Linux runner handling:
#   - This script will reach `ensure_cmd` with no apt-get available.
#   - The preflight step will fail clearly, blocking the probe.
#   - This is intentional: fail visibly rather than run a silent no-op.
#
# To add macOS support in future: add a Homebrew branch before ensure_cmd.
# To add Windows support: add a Chocolatey/winget branch.
# See: scripts/tools/RUNNER_SUPPORT_POLICY.md for the full policy and expansion path.
# See: tools_server/RELIABILITY_POLICY.md (Environment Dependency Policy section).
# ============================================================
#
# Optional env vars:
# - SIMULATE_MISSING_CMDS: comma-separated commands treated as missing (for replay tests)
# - DRY_RUN: 1 to print install actions without executing apt-get

SIMULATE_MISSING_CMDS="${SIMULATE_MISSING_CMDS:-}"
DRY_RUN="${DRY_RUN:-0}"

if [[ "${DRY_RUN}" != "0" ]]; then
  echo "[probe-preflight] DRY_RUN enabled"
fi

is_simulated_missing() {
  local cmd="$1"
  if [[ -z "${SIMULATE_MISSING_CMDS}" ]]; then
    return 1
  fi
  IFS=',' read -r -a _items <<< "${SIMULATE_MISSING_CMDS}"
  for item in "${_items[@]}"; do
    if [[ "${item}" == "${cmd}" ]]; then
      return 0
    fi
  done
  return 1
}

is_cmd_available() {
  local cmd="$1"
  if is_simulated_missing "${cmd}"; then
    return 1
  fi
  command -v "${cmd}" >/dev/null 2>&1
}

run_or_echo() {
  if [[ "${DRY_RUN}" != "0" ]]; then
    echo "[probe-preflight] DRY-RUN: $*"
  else
    "$@"
  fi
}

ensure_cmd() {
  local cmd="$1"
  local package="$2"
  if is_cmd_available "${cmd}"; then
    echo "[probe-preflight] ${cmd} already available"
    return
  fi
  echo "[probe-preflight] ${cmd} missing, installing package: ${package}"
  run_or_echo sudo apt-get install -y "${package}"
}

need_update=0
if ! is_cmd_available lsof; then
  need_update=1
fi
if ! is_cmd_available pgrep; then
  need_update=1
fi
if [[ "${need_update}" -eq 1 ]]; then
  echo "[probe-preflight] running apt-get update"
  run_or_echo sudo apt-get update
fi

ensure_cmd lsof lsof
ensure_cmd pgrep procps

if is_cmd_available lsof; then
  echo "[probe-preflight] lsof: $(command -v lsof)"
else
  echo "[probe-preflight] lsof unresolved (simulated missing)"
fi

if is_cmd_available pgrep; then
  echo "[probe-preflight] pgrep: $(command -v pgrep)"
else
  echo "[probe-preflight] pgrep unresolved (simulated missing)"
fi

if [[ "${DRY_RUN}" == "0" ]]; then
  command -v lsof >/dev/null 2>&1 || {
    echo "[probe-preflight] FAIL: lsof still missing after preflight" >&2
    exit 1
  }
  command -v pgrep >/dev/null 2>&1 || {
    echo "[probe-preflight] FAIL: pgrep still missing after preflight" >&2
    exit 1
  }
fi

echo "[probe-preflight] PASS"
