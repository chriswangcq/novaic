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
run_check "complex-problem-tmp-lint" "$PYTHON_BIN" scripts/ci/lint_complex_problem_tmp.py
run_check "runtime-worker-supervision-lint" "$PYTHON_BIN" scripts/ci/lint_runtime_worker_supervision.py
run_check "deploy-fresh-smoke-lint" "$PYTHON_BIN" scripts/ci/lint_deploy_fresh_smoke.py
run_check "image-namespace-deploy-lint" "$PYTHON_BIN" scripts/ci/lint_image_namespace_deploy.py
run_check "immutable-image-workflows-lint" "$PYTHON_BIN" scripts/ci/lint_immutable_image_workflows.py
run_check "namespace-platform-docs-lint" "$PYTHON_BIN" scripts/ci/lint_namespace_platform_docs.py
run_check "api-backend-compose-path-lint" "$PYTHON_BIN" scripts/ci/lint_api_backend_compose_path.py
run_check "api-backend-namespace-compose-lint" "$PYTHON_BIN" scripts/ci/lint_api_backend_namespace_compose.py
run_check "host-infra-compose-path-lint" "$PYTHON_BIN" scripts/ci/lint_host_infra_compose_path.py
run_check "llm-factory-docker-path-lint" "$PYTHON_BIN" scripts/ci/lint_llm_factory_docker_path.py
run_check "llm-factory-namespace-compose-lint" "$PYTHON_BIN" scripts/ci/lint_llm_factory_namespace_compose.py
run_check "release-controller-ci-guard" "$PYTHON_BIN" -m pytest -q scripts/ci/test_release_controller_ci.py
run_check "service-config-secret-split-lint" "$PYTHON_BIN" scripts/ci/lint_service_config_secret_split.py
run_check "service-catalog-discovery-lint" "$PYTHON_BIN" scripts/ci/lint_service_catalog_discovery.py
run_check "namespace-registry-runtime-lint" "$PYTHON_BIN" scripts/ci/lint_namespace_registry_runtime.py
run_check "retired-runtime-vocabulary-lint" "$PYTHON_BIN" scripts/ci/lint_retired_runtime_vocabulary.py
run_check "start-config-contract-lint" "$PYTHON_BIN" scripts/ci/check_start_config_contract.py
run_pytest "sandbox-sdk" "novaic-sandbox-sdk" "."
run_pytest "logicalfs" "novaic-logicalfs" ".:../novaic-common:../novaic-blob-service"
run_pytest "agent-runtime" "novaic-agent-runtime" ".:../novaic-common"
run_pytest "business" "novaic-business" ".:../novaic-common"
run_pytest "common" "novaic-common" ".:../novaic-agent-runtime"
run_pytest "sandbox-service" "novaic-sandbox-service" ".:../novaic-sandbox-sdk:../novaic-common"
run_pytest "cortex" "novaic-cortex" ".:../novaic-logicalfs:../novaic-sandbox-sdk:../novaic-common"
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
