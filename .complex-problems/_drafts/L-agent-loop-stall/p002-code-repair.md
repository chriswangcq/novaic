# Code repair for identified stall cause

## Problem

Implement the smallest deterministic code change that fixes the root cause discovered in live diagnosis. Avoid compatibility fallbacks or masking behavior; the repaired harness should progress or fail explicitly.

## Success Criteria

- The responsible module is patched.
- Regression tests cover the failing transition or state.
- Local targeted tests pass.
- The diff is reviewed for hidden fallback, stale branch, or unclear dependency boundary.
