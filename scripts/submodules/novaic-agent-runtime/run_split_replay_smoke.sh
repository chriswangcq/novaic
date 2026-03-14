#!/usr/bin/env bash
set -euo pipefail

echo "[split-agent-runtime] Running split wiring replay smoke..."
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
PYTHONPATH="." pytest -q "tests/unit/task_queue/test_retry_policy_and_idempotency.py"
echo "[split-agent-runtime] SPLIT_WIRING_REPLAY_PASS"
