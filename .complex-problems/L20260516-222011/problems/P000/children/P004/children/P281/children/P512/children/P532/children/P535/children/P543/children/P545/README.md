# Classify low-density tests with 2-4 hits

## Problem

Classify the low-density remainder test files that have 2-4 P531 static-residue hits each. This bucket contains 43 hits across 17 files after subtracting P541 and P542 ownership.

Initial file group:
- `tests/test_pr236_session_fsm_decision.py`
- `tests/test_pr243_inbox_restart_cutover.py`
- `tests/integration/test_depends_on_prev_result.py`
- `tests/test_finalize_summary_boundary.py`
- `tests/test_pr277_session_outbox_required_saga_orchestrator.py`
- `tests/test_pr306_taskqueue_fsm_cutover.py`
- `tests/test_pr43_last_scope_wiring.py`
- `tests/test_pr235_session_ledger.py`
- `tests/test_pr237_session_outbox_observe.py`
- `tests/test_pr270_session_finalize_ledger_boundary.py`
- `tests/test_pr284_session_event_vocabulary.py`
- `tests/test_pr313_worker_lease_cutover.py`
- `tests/test_pr48_turn_finalizer.py`
- `tests/test_pr57_prev_scope_history_inject.py`
- `tests/test_pr65_agent_root_scope.py`
- `tests/test_pr67_wake_child_scope.py`
- `tests/test_pr85_llm_context_smoke_guardrails.py`

## Success Criteria

- The 2-4-hit low-density bucket is counted and reconciled.
- Every listed file has a classification rationale.
- Stale or misleading tests become follow-up-worthy.
- The bucket records artifacts for P543/P544 reconciliation.
