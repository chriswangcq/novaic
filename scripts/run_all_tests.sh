#!/usr/bin/env bash
# Canonical backend test matrix for the NovAIC monorepo.
#
# Do not run bare `pytest` across the repository root: submodules are separate
# Python packages and several contract tests intentionally import sibling
# services. This runner makes those dependency edges explicit per module.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider"

PASSED=()
FAILED=()

cleanup_generated_python_artifacts() {
    find "$ROOT" \
        \( \
            -path "$ROOT/.git" -o -path "$ROOT/*/.git" -o \
            -path "$ROOT/node_modules" -o -path "$ROOT/*/node_modules" -o \
            -path "$ROOT/target" -o -path "$ROOT/*/target" -o \
            -path "$ROOT/.venv" -o -path "$ROOT/*/.venv" -o \
            -path "$ROOT/thirdparty" -o -path "$ROOT/*/target" -o \
            -path "$ROOT/novaic-app/src-tauri/gen/apple/build" \
        \) -prune -o \
        \( \
            -type d \( -name '__pycache__' -o -name '.pytest_cache' -o -name '*.egg-info' \) -o \
            -type f -name '*.pyc' \
        \) -print0 | xargs -0 rm -rf
}

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
run_check "runtime-worker-supervision-lint" "$PYTHON_BIN" scripts/ci/lint_runtime_worker_supervision.py
run_check "deploy-fresh-smoke-lint" "$PYTHON_BIN" scripts/ci/lint_deploy_fresh_smoke.py
run_check "retired-runtime-vocabulary-lint" "$PYTHON_BIN" scripts/ci/lint_retired_runtime_vocabulary.py
run_check "start-config-contract-lint" "$PYTHON_BIN" scripts/ci/check_start_config_contract.py
run_pytest "agent-runtime" "novaic-agent-runtime" ".:../novaic-common"
run_pytest "business" "novaic-business" ".:../novaic-common"
run_pytest "common" "novaic-common" ".:../novaic-agent-runtime"
run_pytest "cortex" "novaic-cortex" ".:../novaic-common"
run_pytest "blob-service" "novaic-blob-service" ".:../novaic-common"
run_pytest "llm-factory" "novaic-llm-factory" "."
cleanup_generated_python_artifacts
run_check "generated-artifacts-lint" scripts/ci/lint_generated_artifacts.sh

echo ""
echo "========== SUMMARY =========="
echo "Passed: ${#PASSED[@]} - ${PASSED[*]:-none}"
echo "Failed: ${#FAILED[@]} - ${FAILED[*]:-none}"

if [[ ${#FAILED[@]} -gt 0 ]]; then
    exit 1
fi
