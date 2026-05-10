# Write event-source context design and construction plan

## Problem Definition

Phase 0 must create the final design documentation for the Cortex context event-source cutover before any substrate/write/read migration begins.

## Proposed Solution

- Inspect current Cortex docs and active code path.
- Add a design document under `docs/cortex/` defining the full event-source target architecture.
- Include event envelope, event types, stream identity, ordering/idempotency, projections, no-compat reset policy, cutover phases, and verification gates.
- Keep this phase documentation-only except for ledger files.

## Acceptance Criteria

- A design document exists in the repository.
- The document states that context events are the target source of truth.
- The document states old historical data may be deleted/reset and no old data migration is required.
- The document names legacy DFS files as projections/debug views after cutover, not source.
- The construction plan maps to child phases P002-P006.

## Verification Plan

- Read the new document and check required sections.
- Verify no implementation files are changed by Phase 0.
- Record result and run strict success check.

## Risks

- A vague design document would allow future half-migrations.
- If the document leaves DFS files as co-equal truth, it violates the user's explicit cutover direction.

## Assumptions

- Existing old context data can be wiped during deployment/cutover.
- Projection files may still exist for shell/RO/debug compatibility, but only as derived views.
