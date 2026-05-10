# Mark legacy filesystem writes as projections

## Problem Definition

After event cutover, active endpoints still call generic Workspace methods like `append_context`, `write_step`, and `complete_child_scope`. Even if events are emitted first, these names imply legacy files are still source-of-truth writes.

## Proposed Solution

- Add projection-named Workspace methods for transitional context, step, and skill lifecycle file writes.
- Route event-wired API endpoints through projection-named methods after event append.
- Keep underlying file behavior unchanged for transitional readers.
- Add or run tests to ensure no behavior regression.

## Acceptance Criteria

- `context_append` / `context_batch` use context projection methods.
- `steps_write` uses step projection method.
- `context_skill_end` uses skill close projection method.
- Existing tests continue to pass.
- Static scans can distinguish active event append calls from projection writes.

## Verification Plan

- Run focused event API tests.
- Run full Cortex suite.
- Static scan relevant API calls.

## Risks

- This is a naming/routing demotion, not final projection deletion.

## Assumptions

- Read cutover will later delete or further isolate the projection methods.
