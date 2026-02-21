#!/usr/bin/env bash
# gate_round010.sh — Round 010 gate runner
# Runs all audit scripts in order; exits non-zero on first failure.
# Prints ROUND010_GATE_RUNNER_PASS when all checks succeed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$SCRIPT_DIR/repos/novaic-evidence-audit/scripts"

run_step() {
  local name="$1"; shift
  echo "── [gate_round010] running: $name ──"
  python3 "$@"
  echo "   ✓ $name PASS"
  echo ""
}

run_step "canonical-url-audit"      "$SCRIPTS/enforce_canonical_repo_url.py"
run_step "commit-reachability-audit" "$SCRIPTS/check_commit_reachability.py"
run_step "cross-team-evidence-audit" "$SCRIPTS/audit_round010_reports.py"
run_step "regression-safety-audit"  "$SCRIPTS/regression_check_prior_green_teams.py"
run_step "negative-fixture-tests"   "$SCRIPTS/test_negative_fixtures.py"

echo "ROUND010_GATE_RUNNER_PASS"
