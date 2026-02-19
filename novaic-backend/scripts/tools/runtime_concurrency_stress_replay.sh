#!/usr/bin/env bash
set -euo pipefail

# Replay concurrent lifecycle contention tests multiple rounds
# and emit deterministic summary for report evidence.

ROUNDS="${1:-20}"

if ! [[ "$ROUNDS" =~ ^[0-9]+$ ]] || [[ "$ROUNDS" -le 0 ]]; then
  echo "usage: $0 [positive_round_count]"
  exit 1
fi

TEST_1="tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py::test_concurrent_get_or_create_returns_single_active_runtime"
TEST_2="tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py::test_concurrent_status_cas_allows_single_winner"

pass_count=0
for i in $(seq 1 "$ROUNDS"); do
  echo "[runtime-stress] round ${i}/${ROUNDS}"
  pytest -q "$TEST_1" "$TEST_2" >/tmp/runtime-stress-round.log
  pass_count=$((pass_count + 1))
done

echo "runtime_stress_replay_rounds=${ROUNDS}"
echo "runtime_stress_replay_passed_rounds=${pass_count}"
echo "runtime_stress_replay_status=PASS"

