#!/usr/bin/env bash
# Canonical backend test matrix for the NovAIC monorepo.
#
# Do not run bare `pytest` across the repository root: submodules are separate
# Python packages and several contract tests intentionally import sibling
# services. This runner makes those dependency edges explicit per module.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

PASSED=()
FAILED=()

run_check() {
    local name="$1"
    shift

    echo ""
    echo "========== ${name} =========="
    if (cd "$ROOT" && "$@"); then
        PASSED+=("$name")
        echo "[PASS] ${name}"
    else
        FAILED+=("$name")
        echo "[FAIL] ${name}"
    fi
}

run_pytest() {
    local name="$1"
    local dir="$2"
    local pythonpath="$3"
    shift 3

    echo ""
    echo "========== ${name} =========="
    if (cd "$ROOT/$dir" && PYTHONPATH="$pythonpath" "$PYTHON_BIN" -m pytest -q "$@"); then
        PASSED+=("$name")
        echo "[PASS] ${name}"
    else
        FAILED+=("$name")
        echo "[FAIL] ${name}"
    fi
}

run_check "root-ci-guards" "$PYTHON_BIN" -m pytest -q
run_pytest "agent-runtime" "novaic-agent-runtime" ".:../novaic-common"
run_pytest "business" "novaic-business" ".:../novaic-common"
run_pytest "common" "novaic-common" ".:../novaic-agent-runtime"
run_pytest "cortex" "novaic-cortex" ".:../novaic-common"
run_pytest "blob-service" "novaic-blob-service" ".:../novaic-common"
run_pytest "llm-factory" "novaic-llm-factory" "."

echo ""
echo "========== SUMMARY =========="
echo "Passed: ${#PASSED[@]} - ${PASSED[*]:-none}"
echo "Failed: ${#FAILED[@]} - ${FAILED[*]:-none}"

if [[ ${#FAILED[@]} -gt 0 ]]; then
    exit 1
fi
