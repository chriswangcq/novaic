# Classify cutover and guardrail test residue hits

## Problem

Classify high-density test residue hits in cutover, SSOT, guardrail, and cleanup tests. This group covers tests whose purpose is to prevent old queue/session paths, legacy compatibility, active-session table ownership, and direct side-effect branches from returning.

Initial file group:
- `tests/test_pr153_pending_inbox_metadata.py`
- `tests/test_pr315_queue_fsm_final_residue_guard.py`
- `tests/test_pr251_wake_creation_outbox_cutover.py`
- `tests/test_pr252_session_state_ssot.py`
- `tests/test_pr255_legacy_compat_cleanup.py`
- `tests/test_pr257_remove_active_sessions_table.py`
- `tests/test_pr273_session_harness_final_residue_guard.py`
- `tests/test_pr248_attach_outbox_cutover.py`
- `tests/test_pr272_session_active_state_ledger_boundary.py`
- `tests/test_pr316_taskqueue_state_candidate_cutover.py`
- `tests/integration/test_saga_dag_refactor.py`

## Success Criteria

- Hits for this file group are counted and reconciled against P531 test scan lines.
- Each file gets a purpose/category rationale.
- Guardrail tests are preserved when they intentionally mention retired vocabulary.
- Any stale or misleading guardrail/cutover test becomes a follow-up.
