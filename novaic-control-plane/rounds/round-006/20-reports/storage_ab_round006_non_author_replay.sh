#!/usr/bin/env bash
# Non-author replay script for Storage-A/B Round 006
# Run from any directory with workspace root set via WORKSPACE_ROOT env, or defaults to $HOME/novaic
set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/novaic}"
ROOT_A="$WORKSPACE_ROOT/novaic-storage-a"
ROOT_B="$WORKSPACE_ROOT/novaic-storage-b"
REPORT_DIR="$WORKSPACE_ROOT/novaic-control-plane/rounds/round-006/20-reports"

echo "=== Storage-A/B Round 006 Non-Author Replay ==="
echo "workspace_root=$WORKSPACE_ROOT"
echo ""

# ---- Step 1: Storage-A smoke ----
echo "[1/4] Storage-A smoke..."
cd "$ROOT_A"
bash scripts/smoke_storage_a.sh | tee /tmp/storage_a_smoke_r6.log
grep -q "STORAGE_A_SMOKE_OK=true" /tmp/storage_a_smoke_r6.log || { echo "REPLAY_STORAGE_A_SMOKE=FAIL"; exit 1; }
echo "REPLAY_STORAGE_A_SMOKE=PASS"
echo ""

# ---- Step 2: Storage-B restore validate ----
echo "[2/4] Storage-B restore validate..."
cd "$ROOT_B"
bash scripts/validate_storage_b_restore.sh | tee /tmp/storage_b_restore_r6.log
grep -q "STORAGE_B_RESTORE_VALIDATE=PASS" /tmp/storage_b_restore_r6.log || { echo "REPLAY_STORAGE_B_RESTORE=FAIL"; exit 1; }
echo "REPLAY_STORAGE_B_RESTORE=PASS"
echo ""

# ---- Step 3: Storage-B smoke ----
echo "[3/4] Storage-B smoke..."
cd "$ROOT_B"
bash scripts/smoke_storage_b.sh | tee /tmp/storage_b_smoke_r6.log
grep -q "STORAGE_B_SMOKE_OK=true" /tmp/storage_b_smoke_r6.log || { echo "REPLAY_STORAGE_B_SMOKE=FAIL"; exit 1; }
echo "REPLAY_STORAGE_B_SMOKE=PASS"
echo ""

# ---- Step 4: Failure-injection cross-repo retry chain ----
echo "[4/4] Failure-injection cross-repo retry chain..."
cd "$ROOT_B"
bash scripts/failure_injection_cross_repo_retry.sh | tee /tmp/storage_ab_retry_r6.log
grep -q "STORAGE_AB_RETRY_INJECTION=PASS" /tmp/storage_ab_retry_r6.log || { echo "REPLAY_RETRY_INJECTION=FAIL"; exit 1; }
grep -q "RETRY_ATTEMPT_LOG=PASS" /tmp/storage_ab_retry_r6.log || { echo "REPLAY_RETRY_LOG=FAIL"; exit 1; }
echo "REPLAY_RETRY_INJECTION=PASS"
echo ""

echo "=== ALL STORAGE-A/B ROUND 006 REPLAY CHECKS PASSED ==="
echo "STORAGE_AB_ROUND006_REPLAY=PASS"
