# Verify skill lifecycle cutover boundaries

## Problem Definition

After P038/P039, lifecycle events are emitted, but remaining filesystem writes for child scopes, `summary.md`, indexes, and meta phase changes must be audited and classified before the parent P027 can close.

## Proposed Solution

- Run focused lifecycle event tests and full Cortex suite.
- Static scan lifecycle write sites:
  - `context_skill_begin`;
  - `context_skill_end`;
  - `Workspace.create_scope`;
  - `Workspace.complete_child_scope`;
  - `summary.md`, child scope `_index.jsonl`, and meta phase writes.
- Classify each remaining direct write as transitional projection, payload-independent support, or true direct-only lifecycle bypass.

## Acceptance Criteria

- Focused lifecycle event tests pass.
- Full Cortex suite passes.
- Static scans document remaining lifecycle writes.
- No unclassified direct-only lifecycle bypass remains.
- If a true gap is found, create a follow-up.

## Verification Plan

- Run lifecycle/projection/writer focused tests.
- Run full Cortex suite.
- Run `rg` scans for lifecycle write patterns.
- Record classification in the result.

## Risks

- Static scanning can miss dynamic path writes; mitigate by scanning both API endpoints and Workspace methods.

## Assumptions

- Legacy lifecycle files remain transitional until cleanup/read-cutover phases.
