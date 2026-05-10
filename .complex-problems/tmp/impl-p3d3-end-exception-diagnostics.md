# Skill End Exception Diagnostic Cleanup

## Problem

`context_skill_end` uses SQLite projection for normal empty/mismatch/success decisions, but its exception branch still falls back to `_collect_active_stack(...)` to build diagnostic response data. Exception diagnostics can become future authority if left as old file-walk residue.

This belongs under Phase 3D because `skill_end` is a core LIFO path and the remaining file-walk usage is isolated to its failure/diagnostic branch.

## Success Criteria

- `skill_end` exception responses use the projection frames captured at function entry, or a clearly non-authoritative empty diagnostic if projection read itself failed.
- `context_skill_end` contains no `_collect_active_stack(...)` calls.
- Existing `missing_scope_id`, `stack_empty`, `scope_mismatch`, and success API semantics are preserved.
- Tests cover an injected close failure and assert the error response reports projection-derived `actual_stack_top` / stack data without file-walk fallback.
