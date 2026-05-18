# Ticket: Audit runtime attach handler generation enforcement

## Problem Definition

Verify runtime `session.attach_input` handling requires expected wake scope and expected session generation, reads current wake metadata from Cortex, and rejects stale/missing values before mutating context or claiming IM notifications.

## Proposed Solution

Inspect `task_queue/handlers/runtime_handlers.py::handle_session_attach_input` and its tests. Run focused runtime attach tests. If missing/stale generation or stale scope can mutate context, fix the handler and add regression coverage.

## Acceptance Criteria

- Runtime handler current wake/scope/generation source is mapped.
- Missing expected wake scope and missing expected generation are rejected.
- Stale wake scope and stale generation are rejected before append/claim.
- Focused tests prove the enforcement behavior.

## Verification Plan

Run source search for `handle_session_attach_input`, `expected_session_generation`, `current_session_generation`, and `current_wake_scope_id`. Run focused tests in `test_pr238_generation_checked_attach.py`, `test_pr233_active_inbox_dispatch.py`, and `test_pr255_legacy_compat_cleanup.py`.

## Risks

- Handler tests may use mocked bridge behavior that misses ordering between validation and mutation.
- Scope enforcement and generation enforcement may each be correct alone but incomplete together.

## Assumptions

- Runtime handler is the final fail-closed boundary before modifying Cortex context/inbox.
