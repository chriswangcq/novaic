#!/usr/bin/env bash
# =============================================================================
# storage-ab-round010-replay-bundle.sh
# Round 010 - Storage-A/B Clean-Clone Operability Replay Bundle
#
# Canonical repos (remote-first, no local sibling dependency):
#   https://github.com/chriswangcq/novaic-storage-a  sha=8a0595af3616d1b25300c43c660a13e461c34097
#   https://github.com/chriswangcq/novaic-storage-b  sha=03065c9ed42a83e24362df3378f9e0495877d5df
#
# Usage (fresh machine, no pre-existing local repos required):
#   bash storage-ab-round010-replay-bundle.sh
#
# Env overrides:
#   CLONE_VIA=ssh       — clone via SSH instead of HTTPS (useful on restricted networks)
#   STORAGE_A_SHA=<sha> — pin to specific commit (default: branch HEAD)
#   STORAGE_B_SHA=<sha> — pin to specific commit
#
# Expected final marker:
#   STORAGE_AB_ROUND010_REPLAY=PASS
# =============================================================================
set -uo pipefail

REPO_A="https://github.com/chriswangcq/novaic-storage-a"
REPO_B="https://github.com/chriswangcq/novaic-storage-b"
BRANCH_A="split/round-003-storage-a"
BRANCH_B="split/round-003-storage-b"
CLONE_VIA="${CLONE_VIA:-https}"

TMP_WORKSPACE="$(mktemp -d "${TMPDIR:-/tmp}/novaic-round010-clone-XXXXXX")"
ROOT_A="$TMP_WORKSPACE/novaic-storage-a"
ROOT_B="$TMP_WORKSPACE/novaic-storage-b"

PASS=0; FAIL=0

cleanup() { rm -rf "$TMP_WORKSPACE" 2>/dev/null || true; }
trap cleanup EXIT

clone_repo() {
  local label="$1" https_url="$2" branch="$3" dest="$4"
  local ssh_url
  ssh_url="git@github.com:${https_url#https://github.com/}.git"
  echo "--- [clone] $label ---"
  if [[ "$CLONE_VIA" == "ssh" ]]; then
    git clone --branch "$branch" --depth 1 "$ssh_url" "$dest" 2>&1 | tail -3
  else
    if git clone --branch "$branch" --depth 1 "$https_url" "$dest" 2>&1 | tail -3; then
      : # https ok
    else
      echo "  HTTPS clone failed, retrying via SSH..."
      git clone --branch "$branch" --depth 1 "$ssh_url" "$dest" 2>&1 | tail -3
    fi
  fi
}

run_step() {
  local label="$1" cmd="$2" marker="$3"
  echo "--- [$label] ---"
  local tmpout; tmpout="$(mktemp)"
  local rc=0
  eval "$cmd" > "$tmpout" 2>&1 || rc=$?
  if grep -q "$marker" "$tmpout"; then
    echo "REPLAY_${label}=PASS"
    PASS=$((PASS+1))
  else
    echo "REPLAY_${label}=FAIL  # marker not found or rc=${rc}"
    tail -8 "$tmpout" | sed 's/^/  /'
    FAIL=$((FAIL+1))
  fi
  rm -f "$tmpout"
}

echo "=== Storage-A/B Round 010 Clean-Clone Replay Bundle ==="
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "clone_workspace=$TMP_WORKSPACE"
echo ""
echo "# Canonical remote repos"
echo "# Storage-A: $REPO_A  branch=$BRANCH_A  sha=8a0595af3616d1b25300c43c660a13e461c34097"
echo "# Storage-B: $REPO_B  branch=$BRANCH_B  sha=03065c9ed42a83e24362df3378f9e0495877d5df"
echo ""

# Clone both repos from GitHub
clone_repo "novaic-storage-a" "$REPO_A" "$BRANCH_A" "$ROOT_A"
clone_repo "novaic-storage-b" "$REPO_B" "$BRANCH_B" "$ROOT_B"

# Install Python deps in each clone
echo "--- [setup] install dependencies ---"
pip install -q -r "$ROOT_A/requirements.txt" 2>&1 | tail -2
pip install -q -r "$ROOT_B/requirements.txt" 2>&1 | tail -2
echo "SETUP_DONE=true"
echo ""

# Run all verification steps from clean clones
run_step "CONTRACT_VERSION_A" \
  "cd \"$ROOT_A\" && bash scripts/verify_contract_version_a.sh" \
  "STORAGE_A_CONTRACT_VERSION=PASS"

run_step "CONTRACT_VERSION_B" \
  "cd \"$ROOT_B\" && bash scripts/verify_contract_version_b.sh" \
  "STORAGE_B_CONTRACT_VERSION=PASS"

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
  "cd \"$ROOT_B\" && STORAGE_A_ROOT=\"$ROOT_A\" bash scripts/failure_injection_cross_repo_retry.sh" \
  "STORAGE_AB_RETRY_INJECTION=PASS"

run_step "MAX_BREACH" \
  "cd \"$ROOT_B\" && bash scripts/failure_injection_max_attempt_breach.sh" \
  "RETRY_MAX_BREACH_STOP=PASS"

echo ""
echo "--- Summary ---"
echo "STEPS_PASSED=$PASS"
echo "STEPS_FAILED=$FAIL"
if [[ "$FAIL" -eq 0 ]]; then
  echo "=== ALL STORAGE-A/B ROUND 010 CLEAN-CLONE REPLAY CHECKS PASSED ==="
  echo "STORAGE_AB_ROUND010_REPLAY=PASS"
else
  echo "STORAGE_AB_ROUND010_REPLAY=FAIL"
  exit 1
fi
