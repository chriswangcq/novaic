# Round 009 Report - Agent Runtime Team

## Task 1 — code/behavior change

- task: `Refactor concurrency threshold config into explicit tiered policy and enforce tier=unit label in PASS/FAIL markers`
- problem_fixed: `Threshold constants were inline per test file with no tier distinction. Unit and integration floors were mixed, making platform audit unable to verify tier-appropriate thresholds.`
- solution_applied: `Created tests/threshold_policy.py with UNIT_* and INTEGRATION_* constant sets. test_high_concurrency_retry_replay.py and test_dedup_guard_failure_path.py now import from this module. PASS/FAIL markers include tier=unit so audit scripts can filter by tier.`
- target_state_proof: `Running the command produces HIGH_CONCURRENCY_RETRY_REPLAY_PASS tier=unit and HIGH_CONCURRENCY_IDEM_DEDUP_PASS tier=unit and exits 0`

- evidence:
  - command: `cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_high_concurrency_retry_replay.py`
  - expected_marker: `HIGH_CONCURRENCY_RETRY_REPLAY_PASS`
  - expected_marker: `tier=unit`
  - expected_marker: `HIGH_CONCURRENCY_IDEM_DEDUP_PASS`
  - expected_marker: `2 passed`
  - repo_url: `https://github.com/novaic/novaic-agent-runtime`
  - commit_sha: `71c9fb2ec5f08a12c83c66a9574cc09d9d1020cb`
  - migrated_paths: `tests/threshold_policy.py`
  - migrated_paths: `tests/unit/task_queue/test_high_concurrency_retry_replay.py`
  - artifact_path: `novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md`

- status: DONE

---

## Task 2 — failure-path replay

- task: `Confirm dedup-guard-broken replay emits DEDUP_GUARD_BROKEN with tier=unit label`
- problem_fixed: `DEDUP_GUARD_BROKEN marker had no tier label; cross-team audit could not distinguish unit vs integration failure-path runs.`
- solution_applied: `test_dedup_guard_failure_path.py imports UNIT_TIER_LABEL from tests.threshold_policy and includes tier=unit in DEDUP_GUARD_BROKEN marker output.`
- target_state_proof: `Running the command produces DEDUP_GUARD_BROKEN tier=unit and exits 0`

- evidence:
  - command: `cd /Users/wangchaoqun/novaic/novaic-agent-runtime && PYTHONPATH="." pytest -q -s tests/unit/task_queue/test_dedup_guard_failure_path.py`
  - expected_marker: `DEDUP_GUARD_BROKEN`
  - expected_marker: `tier=unit`
  - expected_marker: `1 passed`
  - repo_url: `https://github.com/novaic/novaic-agent-runtime`
  - commit_sha: `71c9fb2ec5f08a12c83c66a9574cc09d9d1020cb`
  - migrated_paths: `tests/unit/task_queue/test_dedup_guard_failure_path.py`
  - artifact_path: `novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md`

- status: DONE

---

## Task 3 — operability artifact

- task: `Publish agent-runtime-round009-evidence.md with tier config table, replay commands, output markers, and CI usage notes`
- problem_fixed: `Prior evidence bundles had no CI usage notes and no tier config table. Non-author could not know how to override thresholds in CI.`
- solution_applied: `Wrote novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md with: tiered threshold table, per-task actual output blocks, copy-paste CI replay commands, CI usage note on PYTHONPATH and threshold override, metrics PASS/FAIL table, and grep audit marker table.`
- target_state_proof: `grep command returns non-empty output for all five required markers`

- evidence:
  - command: `grep -E "HIGH_CONCURRENCY_RETRY_REPLAY_PASS|HIGH_CONCURRENCY_IDEM_DEDUP_PASS|DEDUP_GUARD_BROKEN|SPLIT_REPO_ALL_PASS|tier=unit" /Users/wangchaoqun/novaic/novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md`
  - expected_marker: `HIGH_CONCURRENCY_RETRY_REPLAY_PASS`
  - expected_marker: `HIGH_CONCURRENCY_IDEM_DEDUP_PASS`
  - expected_marker: `DEDUP_GUARD_BROKEN`
  - expected_marker: `SPLIT_REPO_ALL_PASS`
  - expected_marker: `tier=unit`
  - repo_url: `https://github.com/novaic/novaic-agent-runtime`
  - commit_sha: `71c9fb2ec5f08a12c83c66a9574cc09d9d1020cb`
  - migrated_paths: `novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md`
  - artifact_path: `novaic-control-plane/rounds/round-009/split-close/agent-runtime-round009-evidence.md`

- status: DONE

---

## Questions For Program Owner

- question: `Is the INTEGRATION tier threshold policy (floor=500 ops/s) aligned with expected integration test infra performance, or should a different baseline be used?`
- why_blocking: `Integration tests have not been run from the split repo yet. The floor=500 is estimated from Round 004 baseline (~1199 ops/s with 40% margin). If integration infra changes, this floor may need adjustment before integration tier tests are added.`
- options: `(a) keep floor=500 as conservative estimate; (b) program owner specifies integration floor from observed CI runs; (c) defer integration tier tests to a future round`
- recommended_option: `(b) program owner specifies floor after first integration CI run`
- impact_if_unanswered: `Integration tier constants remain at estimated floor=500; unit tier is unaffected`
- requested_by_round: `round-010`

---

## Team status

- status: DONE
- blocker: NONE
