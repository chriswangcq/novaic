# Phase 3E Active Stack Cutover Verification

## Problem

The active-stack/status cutover needs a final verification pass proving SQLite is authoritative and that old file-walk control paths are gone.

## Success Criteria

- Targeted tests cover nesting, mismatch, finalize/open-child behavior, restart recovery, and status reads.
- Static residue search proves runtime active-stack authority no longer depends on `_collect_active_stack` or equivalent file walking.
- Broader Cortex targeted tests and `py_compile` pass.
- Any remaining stack-related file projection code is documented as trace/repair/debug, not runtime authority.
