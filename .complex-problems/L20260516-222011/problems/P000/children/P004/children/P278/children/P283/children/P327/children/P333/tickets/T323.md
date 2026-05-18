# Ticket: Audit aggregate stale/missing attach generation regression coverage

## Problem Definition

Review repository, outbox, and runtime attach generation coverage as one chain. Ensure stale or missing generation cannot pass through any layer and that the tests cover both malformed payload rejection and stale-session race behavior.

## Proposed Solution

Map existing tests by layer, run the full attach-generation focused suite after P330-P332 changes, and add any missing guard that would allow stale/missing attach generation to regress. Record the coverage matrix and remaining gaps.

## Acceptance Criteria

- Coverage matrix lists repository, outbox, and runtime attach generation tests.
- Focused attach generation test suite passes.
- Source guard confirms old repository generation fallback helpers are gone.
- Any uncovered stale/missing generation path is fixed or made a follow-up.

## Verification Plan

Run focused tests covering attach repository behavior, outbox delivery, runtime handler, session state SSOT, active inbox dispatch, and legacy compatibility cleanup. Run source searches for removed helpers and fallback tokens relevant to attach generation.

## Risks

- Individual layer tests can pass while end-to-end semantics still have a gap.
- Source guards can be too broad or too narrow; use them only as support, not sole evidence.

## Assumptions

- P330-P332 are already closed and their changes are present in the working tree.
