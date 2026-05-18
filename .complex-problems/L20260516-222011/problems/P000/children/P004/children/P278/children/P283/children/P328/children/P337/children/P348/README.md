# Runtime finalize handler inventory

## Problem

Map all runtime/task handlers and saga contracts that can process finalize/session-ended/skill-end/recovery completion and identify which ones mutate Cortex, queue state, message claims, or wake/session state.

## Success Criteria

- List live handler/contract files and functions.
- Mark each path as mutating or non-mutating.
- Identify required identity fields for each mutating path.
- Produce implementation targets for the remaining P337 children.
