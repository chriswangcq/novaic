# Cortex Archive Diagnostics Aggregate Verification

## Problem

After source mapping, boundary propagation, and persistence changes, P368 needs an end-to-end style verification that no old inferred archive diagnostics path remains active.

## Success Criteria

- Runs focused runtime and Cortex tests covering the full scope-end diagnostics path.
- Runs compile checks for changed runtime and Cortex modules.
- Runs residue search for `scope_end`, `finalize_reason`, `session_generation`, `remaining_stack`, archive event writers, and active-generation inference.
- Confirms P368 acceptance criteria are all mapped to evidence.

## Why Under P368

This child is the final guard against half-integrated changes where new code exists but active paths still use the old archive behavior.
