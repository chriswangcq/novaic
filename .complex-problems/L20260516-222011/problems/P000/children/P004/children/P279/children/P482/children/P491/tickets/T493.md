# Recovery and session-ended compatibility cleanup ticket

## Problem Definition

P491 must clean the recovery/session-ended compatibility residue identified by P488. Suspected-dead and recovery archive paths currently risk losing stack diagnostics and then synthesizing an empty stack, which can make a broken wake look cleanly recoverable instead of explicitly archived with its remaining stack state.

## Proposed Solution

Split the work into inventory, implementation, and verification. First inspect recovery/session-ended production paths and tests. Then tighten suspected-dead/recovery payload semantics so stack diagnostics are explicit and generation-aware, removing or constraining empty-stack fallbacks. Finally run focused recovery/session-ended tests and guard sweeps.

## Acceptance Criteria

- Recovery and session-ended production paths are inspected and classified.
- Suspected-dead/recovery archive payloads preserve explicit stack diagnostics or fail/mark unknown explicitly.
- Any fallback empty-stack behavior is removed or proven to be guarded, explicit, and non-silent.
- Focused recovery/session-ended tests pass.

## Verification Plan

- Inspect `queue_service/saga_repo.py`, `queue_service/session_recovery.py`, `queue_service/session_repo.py`, `queue_service/session_fsm.py`, `task_queue/handlers/session_handlers.py`, and recovery/finalize tests.
- Run focused tests around recovery, suspected-dead, finalize ownership, and legacy compatibility cleanup.
- Save raw guard output and classification artifacts under `.complex-problems/L20260516-222011/tmp/p491/`.

## Risks

- Recovery code may intentionally need a defensive unknown-stack representation when a crashed wake never produced stack data.
- Tightening payload shape can require test fixture updates across recovery and compensation tests.

## Assumptions

- P489 already removed finalize producer stack fabrication; P491 focuses on suspected-dead/recovery paths.
