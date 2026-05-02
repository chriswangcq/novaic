#!/usr/bin/env bash
# 高强度全面测试 - 遍历各 repo 执行 pytest
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# 使用 agent-runtime 的 venv（包含完整依赖）
VENV_PYTHON="${ROOT}/novaic-agent-runtime/.venv/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Warning: agent-runtime venv not found, using system python"
    VENV_PYTHON="python"
fi

FAILED=()
PASSED=()

run_guard() {
    local name="$1"
    local cmd="$2"
    echo ""
    echo "========== $name =========="
    if eval "$cmd" 2>&1; then
        PASSED+=("$name")
        echo "[PASS] $name"
        return 0
    else
        FAILED+=("$name")
        echo "[FAIL] $name"
        return 1
    fi
}

run_tests() {
    local dir="$1"
    local name="$2"
    local filter="${3:-}"
    if [[ ! -d "$dir" ]]; then
        echo "[SKIP] $name - directory not found"
        return 0
    fi
    echo ""
    echo "========== $name =========="
    local cmd="cd $dir && $VENV_PYTHON -m pip install -r requirements.txt -q 2>/dev/null; $VENV_PYTHON -m pytest tests/ $filter -v --tb=short"
    if eval "$cmd" 2>&1; then
        PASSED+=("$name")
        echo "[PASS] $name"
        return 0
    else
        FAILED+=("$name")
        echo "[FAIL] $name"
        return 1
    fi
}

# 0. root guardrails
run_guard "agent-main-path-acceptance" "scripts/ci/lint_agent_main_path_acceptance.sh" || true
run_guard "retired-agent-paths" "scripts/ci/lint_retired_agent_paths.sh" || true
run_guard "lifecycle-loop-ownership" "scripts/ci/lint_lifecycle_loop_ownership.sh" || true

# 1. agent-runtime (unit)
run_tests "novaic-agent-runtime" "agent-runtime" "tests/unit/" || true

# 2. storage-a
run_tests "novaic-storage-a" "storage-a" "" || true

echo ""
echo "========== SUMMARY =========="
echo "Passed: ${#PASSED[@]} - ${PASSED[*]:-none}"
echo "Failed: ${#FAILED[@]} - ${FAILED[*]:-none}"
[[ ${#FAILED[@]} -eq 0 ]] && exit 0 || exit 1
