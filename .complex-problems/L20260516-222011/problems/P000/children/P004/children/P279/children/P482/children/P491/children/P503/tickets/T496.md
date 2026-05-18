# Recovery/session-ended final verification ticket

## Problem Definition

P503 must verify that P491 recovery/session-ended cleanup is complete after inventory and stack diagnostics hardening. It should prove focused tests pass, legacy recovery stack fallback fields are gone, and remaining recovery/session hits are classified.

## Proposed Solution

Run focused recovery/session-ended/finalize tests together, run final `rg` guard sweeps over production runtime and tests, and save a classification artifact mapping remaining hits to strict production behavior, explicit unknown-stack handling, or test guards.

## Acceptance Criteria

- Focused recovery/session-ended/finalize tests pass.
- Final guard output has no legacy stack fallback fields in runtime/test scope.
- Remaining recovery/session-ended hits are classified.
- Any compatibility-looking hit is either explicit/guarded or routed to follow-up.

## Verification Plan

- Run focused pytest suite for suspected-dead recovery, recovery outbox, finalize ownership, legacy cleanup, and recovery boundary helpers.
- Run guard sweeps for `stack_known_at_finalize`, `stack_depth_at_finalize`, `remaining_stack`, `session_suspected_dead`, `session_ended`, and `recovery_archive`.
- Save a final classification artifact under `.complex-problems/L20260516-222011/tmp/p503/`.

## Risks

- Guard output includes intentional test assertions; classification must not treat test fixtures as production residue.

## Assumptions

- P501 and P502 have already been checked successful.
