#!/usr/bin/env bash
# gate_round008.sh — Round 008 one-command gate runner
#
# Runs all three audit scripts in order:
#   1. enforce_canonical_repo_url.py   (Gate A)
#   2. audit_round008_reports.py       (Gate B + C)
#   3. regression_check_prior_green_teams.py (Gate D regression)
#
# Exits non-zero if ANY audit finds failures.
# Expected PASS marker printed to stdout on success:
#   ROUND008_GATE_RUNNER_PASS
#
# Usage (from workspace root):
#   bash novaic-control-plane/rounds/round-008/split-fix/gate_round008.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_SCRIPTS="${SCRIPT_DIR}/repos/novaic-evidence-audit/scripts"

PYTHON="${PYTHON:-python3}"

run_audit() {
    local name="$1"
    local script="$2"
    echo "── [gate_round008] running: ${name} ──"
    if "${PYTHON}" "${script}"; then
        echo "   ✓ ${name} PASS"
    else
        echo "   ✗ ${name} FAIL — gate_round008 ABORTED" >&2
        exit 1
    fi
}

run_audit "canonical-repo-url-audit" "${AUDIT_SCRIPTS}/enforce_canonical_repo_url.py"
run_audit "cross-team-evidence-audit" "${AUDIT_SCRIPTS}/audit_round008_reports.py"
run_audit "regression-safety-audit"   "${AUDIT_SCRIPTS}/regression_check_prior_green_teams.py"

echo ""
echo "ROUND008_GATE_RUNNER_PASS"
