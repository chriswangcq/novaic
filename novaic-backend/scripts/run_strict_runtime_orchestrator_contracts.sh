#!/usr/bin/env bash
set -euo pipefail

# Run strict Runtime Orchestrator chain contracts with local proxy bypass.
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
export NO_PROXY="localhost,127.0.0.1,::1"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

pytest -q \
  tests/contract/test_runtime_orchestrator_process_startup.py \
  tests/contract/test_internal_api_contract_baseline.py \
  tests/contract/test_internal_vm_vmcontrol_contract.py \
  tests/unit/gateway/test_runtime_orchestrator_startup_contract.py \
  tests/unit/gateway/test_runtime_orchestrator_client.py

