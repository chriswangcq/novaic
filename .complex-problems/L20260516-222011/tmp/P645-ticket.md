# Run Final RW Scratch Focused Tests

## Problem Definition

The final RW scratch cleanup guard needs current-worktree tests proving the layout removal, fixture rewrites, subagent scratch mounting, and lower-layer LogicalFS generic path behavior still work together.

## Proposed Solution

Run the focused Cortex workspace/path/runtime/sandboxd suites and the LogicalFS layout/authority tests with explicit dependency paths. Record commands and outputs. If dependency setup fails, rerun with corrected explicit paths and record both attempts.

## Acceptance Criteria

- Cortex focused tests pass in the current worktree.
- LogicalFS focused tests pass in the current worktree.
- Commands and outputs are recorded.
- Any failure is converted into a follow-up rather than ignored.

## Verification Plan

Run the same aggregate Cortex focused test list used by P640, then run LogicalFS `tests/test_logicalfs.py` and `tests/test_authority.py` with `PYTHONPATH` including `novaic-common`.

## Risks

- Nested repos may need explicit `PYTHONPATH`; missing dependency setup must be recorded, not hidden.
- Focused tests may pass while broader unrelated tests are dirty; this ticket only owns RW scratch cleanup behavior.

## Assumptions

- The residue scan has already classified remaining root scratch strings.
