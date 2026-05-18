# Attach generation contract inventory ticket

## Problem Definition

P496 must inventory active input attach generation contracts. It should prove where expected wake scope and expected session generation are required, and identify any no-generation compatibility residue.

## Proposed Solution

Run targeted searches over attach handler, session outbox, attach effect builder, session repo attach-race logic, session generation helpers, and attach tests. Classify each production hit as strict validation, race buffer, durable outbox payload, test guard, or cleanup candidate.

## Acceptance Criteria

- Raw attach/generation search artifact is saved.
- Classification artifact lists exact file references.
- Missing/ambiguous contracts are explicitly routed to P497 or a spawned child.
- No source changes are made.

## Verification Plan

Use `rg`, `sed`, and focused inspection. Save artifacts under `.complex-problems/L20260516-222011/tmp/p496/`.

## Risks

- Attach-race buffering may look like fallback but is required for correctness.

## Assumptions

- This ticket is read-only inventory.
