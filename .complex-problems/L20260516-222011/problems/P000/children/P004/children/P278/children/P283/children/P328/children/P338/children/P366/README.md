# Child Problem: Finalize Diagnostics Source Map

## Problem

Map every live path that records or forwards `finalize_reason`, `remaining_stack`, `ended_at`, `finalize_generation`, or related session archive metadata.

## Success Criteria

- List production files/functions that construct, forward, persist, or archive these fields.
- Mark each path as mutating or non-mutating.
- Identify which explicit identity fields guard each mutating path.
- Produce precise implementation targets for later child problems.
