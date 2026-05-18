# Ticket: Audit attach expected-generation validation

## Problem Definition

Trace attach input from dispatch through session outbox and runtime handler to verify expected session generation is preserved and enforced. Determine whether missing or stale attach generation can still be accepted, especially when the active scope has changed.

## Proposed Solution

Inspect `SessionRepository` attach request creation, `build_attach_input_effect`, `SessionOutboxDispatcher`, task payload creation, runtime attach handler validation, and existing tests. Run focused attach generation tests and source guards. If a stale or missing generation path is accepted, fix it with the smallest boundary-preserving change and add a regression test.

## Acceptance Criteria

- Attach request creation and outbox payload fields are mapped with file references.
- Outbox worker delivery preserves `expected_session_generation`.
- Downstream handler requires generation and rejects stale generation.
- Scope mismatch or missing-generation attach cannot silently target a newer active generation.
- Verification includes focused attach generation tests and a residue/source guard.

## Verification Plan

Run source searches for `expected_session_generation`, `attach_input`, `current_session_generation`, and `active_generation`. Run focused tests: generation checked attach, attach outbox cutover, active inbox dispatch, session state SSOT, and legacy compat cleanup.

## Risks

- Repository may compute a current generation for an old scope and build a payload that later fails only in runtime, leaving confusing outbox behavior.
- Missing-generation checks may exist in runtime but not in the session outbox boundary.

## Assumptions

- Correct attach behavior is fail-closed: stale or missing generation must not mutate an active wake.
