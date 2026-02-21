#!/usr/bin/env bash
# gate_round009.sh — Round 009 one-command gate runner
#
# Runs all four audit scripts in order:
#   1. enforce_canonical_repo_url.py   (Gate A — https-only)
#   2. check_commit_reachability.py    (Gate B — commit reachability)
#   3. audit_round009_reports.py       (Gate B+C — evidence quality)
#   4. regression_check_prior_green_teams.py (Gate D regression)
#
# Additionally validates negative fixtures pass:
#   5. test_negative_fixtures.py
#
# Exits non-zero if ANY script fails.
# Expected PASS marker: ROUND009_GATE_RUNNER_PASS
#
# Usage (from workspace root):
#   bash novaic-control-plane/rounds/round-009/split-close/gate_round009.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUDIT_SCRIPTS="${SCRIPT_DIR}/repos/novaic-evidence-audit/scripts"
PYTHON="${PYTHON:-python3}"

run_audit() {
    local name="$1"
    local script="$2"
    echo "── [gate_round009] running: ${name} ──"
    if "${PYTHON}" "${script}"; then
        echo "   ✓ ${name} PASS"
    else
        echo "   ✗ ${name} FAIL — gate_round009 ABORTED" >&2
        exit 1
    fi
}

run_audit "canonical-url-audit (https-only)"     "${AUDIT_SCRIPTS}/enforce_canonical_repo_url.py"
run_audit "commit-reachability-audit"             "${AUDIT_SCRIPTS}/check_commit_reachability.py"
run_audit "cross-team-evidence-audit"             "${AUDIT_SCRIPTS}/audit_round009_reports.py"
run_audit "regression-safety-audit"               "${AUDIT_SCRIPTS}/regression_check_prior_green_teams.py"
run_audit "negative-fixture-tests"                "${AUDIT_SCRIPTS}/test_negative_fixtures.py"

echo ""
echo "ROUND009_GATE_RUNNER_PASS"
