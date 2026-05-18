# Audit runtime prepare-context regression coverage

## Problem Definition

The prepare-context implementation is now mapped, but the regression suite must prove stale local continuity and `context.read` projections cannot re-enter final LLM context. Coverage needs to be audited after the source mapping children are complete.

## Proposed Solution

Inventory relevant tests, map each stale-context regression mode to a guard, add any missing guard, and run the selected focused runtime suite.

## Acceptance Criteria

- Prepare-context, ordering, context read-by-id, no-wake replay, no historical tool-image injection, and explicit contract tests are mapped.
- Focused tests are run after source mapping.
- Missing guard coverage is added or split.
- Final result names covered and non-covered stale-context regression modes.

## Verification Plan

Run the selected runtime test slice covering prepare-context authority, context read by-id/order, no-wake replay, no historical image injection, and explicit contracts.

## Risks

- Coverage may be duplicated across tests; this audit must still identify gaps rather than count tests.

## Assumptions

- This can be one-go only if mapping finds no unguarded regression mode after `P160`, `P161`, and `P162` are closed.
