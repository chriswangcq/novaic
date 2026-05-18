# Classify runtime wake continuity residue

## Problem Definition

Wake/session runtime logic may still contain cross-wake, idempotency, no-replay, or notification continuity behavior. These paths must be classified so they cannot act as hidden LLM context fallbacks or replay old user messages into new wakes.

## Proposed Solution

Inspect `runtime_handlers.py` and tests around no-wake replay, child scope, explicit skill summaries, and session recovery. Classify active continuity behavior and run focused tests.

## Acceptance Criteria

- `runtime_handlers.py` and relevant wake continuity call sites are mapped.
- Cross-wake/idempotency/notification replay residues are classified.
- Focused guard tests are identified and run.
- Any stale provider-input or old-message replay path is fixed or split.

## Verification Plan

Run no-wake-replay, explicit skill summary, wake child scope, session recovery boundary, and prepare-context guard tests.

## Risks

- Runtime continuity terms may appear in docs/tests unrelated to active code; classification must separate production call sites from historical test fixtures.

## Assumptions

- Context-read handler itself is already classified by `P173`; this leaf focuses on wake/session runtime continuity.
