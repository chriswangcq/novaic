# Ticket: Finalize Diagnostics Assertion Hardening

## Problem Definition

The queue session finalize path appears to carry explicit finalize diagnostics correctly, but the tests are too loose. A future refactor could accidentally diverge `session_finalized`, `session_closed`, and `session_finalize_rejected` metadata without failing the current suite.

## Proposed Solution

Strengthen `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` around valid finalize, stale generation rejection, and stale scope rejection. Assert exact ledger event generations and payloads, including `finalize_reason`, `finalize_generation`, `ended_scope_id`, and `remaining_stack`. Then rerun focused finalize/restart tests and residue search for ambiguous diagnostics writes.

## Acceptance Criteria

- Valid finalize test asserts `session_finalized` generation and payload include the intended explicit finalize diagnostics.
- Valid finalize test asserts `session_closed` generation and metadata exactly match the explicit finalize metadata.
- Generation mismatch rejection test asserts the active session remains unchanged, no valid finalized event is emitted, and the rejection event records the stale finalize metadata.
- Scope mismatch rejection test asserts the active session remains unchanged, no valid finalized event is emitted, and the rejection event records the stale scope metadata.
- Focused tests for session finalize and pending restart pass.
- Residue search does not reveal direct ambiguous diagnostics writes outside the explicit finalize metadata path.

## Verification Plan

- Run `python3 -m py_compile` on queue session finalize modules and the changed test file.
- Run focused pytest for `tests/test_pr254_finalize_ownership.py`, `tests/test_pr243_inbox_restart_cutover.py`, and `tests/test_pr233_active_inbox_dispatch.py`.
- Run `rg` over queue session finalize modules and changed tests for `finalize_metadata`, `remaining_stack`, `finalize_reason`, and reject/finalized recorders.

## Risks

- Tests may expose a real implementation gap rather than only weak assertions; if so, split another follow-up instead of broadening this ticket silently.
- The assertion hardening could accidentally depend on event ordering beyond the ownership contract; keep assertions scoped to event types and payloads.

## Assumptions

- P366 source map is accurate and the relevant runtime session finalize boundary lives in `novaic-agent-runtime`.
- No production behavior change is intended unless the hardened assertions reveal a defect.
