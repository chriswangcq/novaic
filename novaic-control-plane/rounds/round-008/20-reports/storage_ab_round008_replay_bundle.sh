#!/usr/bin/env bash
# =============================================================================
# storage_ab_round008_replay_bundle.sh
# Round 008 - Storage-A/B Non-Author Operability Replay Package
#
# Canonical URL map:
#   Storage-A: file:///Users/wangchaoqun/novaic/novaic-storage-a
#   Storage-B: file:///Users/wangchaoqun/novaic/novaic-storage-b
#
# Verified commit anchors:
#   novaic-storage-a  branch=split/round-003-storage-a  sha=b7cde077160cb3cfdeb03ba845e5a05cde1f82c7
#   novaic-storage-b  branch=split/round-003-storage-b  sha=c67abaf6286dd2bc369c38c51fab7f8bf4858257
#
# Usage:
#   WORKSPACE_ROOT=/your/path bash storage_ab_round008_replay_bundle.sh
#
# Expected final marker:
#   STORAGE_AB_ROUND008_REPLAY=PASS
# =============================================================================
set -uo pipefail

ROOT="${WORKSPACE_ROOT:-$HOME/novaic}"
ROOT_A="$ROOT/novaic-storage-a"
ROOT_B="$ROOT/novaic-storage-b"

PASS=0; FAIL=0

run_step() {
  local label="$1"; local cmd="$2"; local marker="$3"
  echo "--- [$label] ---"
  local tmpout
  tmpout="$(mktemp)"
  local rc=0
  eval "$cmd" > "$tmpout" 2>&1 || rc=$?
  if grep -q "$marker" "$tmpout"; then
    echo "REPLAY_${label}=PASS"
    PASS=$((PASS+1))
  else
    echo "REPLAY_${label}=FAIL  # marker not found or command failed (rc=${rc})"
    tail -5 "$tmpout" | sed 's/^/  /'
    FAIL=$((FAIL+1))
  fi
  rm -f "$tmpout"
}

echo "=== Storage-A/B Round 008 Non-Author Replay Bundle ==="
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "# Canonical URL map"
echo "# Storage-A: file:///Users/wangchaoqun/novaic/novaic-storage-a  sha=b7cde077160cb3cfdeb03ba845e5a05cde1f82c7"
echo "# Storage-B: file:///Users/wangchaoqun/novaic/novaic-storage-b  sha=c67abaf6286dd2bc369c38c51fab7f8bf4858257"
echo ""

run_step "STORAGE_A_SMOKE" \
  "cd \"$ROOT_A\" && bash scripts/smoke_storage_a.sh" \
  "STORAGE_A_SMOKE_OK=true"

run_step "STORAGE_B_RESTORE" \
  "cd \"$ROOT_B\" && bash scripts/validate_storage_b_restore.sh" \
  "STORAGE_B_RESTORE_VALIDATE=PASS"

run_step "STORAGE_B_SMOKE" \
  "cd \"$ROOT_B\" && bash scripts/smoke_storage_b.sh" \
  "STORAGE_B_SMOKE_OK=true"

run_step "RETRY_INJECTION" \
  "cd \"$ROOT_B\" && bash scripts/failure_injection_cross_repo_retry.sh" \
  "STORAGE_AB_RETRY_INJECTION=PASS"

run_step "MAX_BREACH" \
  "cd \"$ROOT_B\" && bash scripts/failure_injection_max_attempt_breach.sh" \
  "RETRY_MAX_BREACH_STOP=PASS"

echo ""
echo "--- Summary ---"
echo "STEPS_PASSED=$PASS"
echo "STEPS_FAILED=$FAIL"
if [[ "$FAIL" -eq 0 ]]; then
  echo "=== ALL STORAGE-A/B ROUND 008 REPLAY CHECKS PASSED ==="
  echo "STORAGE_AB_ROUND008_REPLAY=PASS"
else
  echo "STORAGE_AB_ROUND008_REPLAY=FAIL"
  exit 1
fi
