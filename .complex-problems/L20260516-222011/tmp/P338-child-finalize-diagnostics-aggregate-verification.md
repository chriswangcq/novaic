# Child Problem: Finalize Diagnostics Aggregate Verification

## Problem

After source map and targeted fixes, verify the full remaining-stack/finalize-reason archive boundary.

## Success Criteria

- Run focused session finalize, Cortex archive, recovery/compensation, and wake-finalize tests.
- Run residue searches for `remaining_stack`, `finalize_reason`, `ended_at`, and generation defaults/active lookup around finalize paths.
- Record any remaining gap as follow-up before closing P338.
