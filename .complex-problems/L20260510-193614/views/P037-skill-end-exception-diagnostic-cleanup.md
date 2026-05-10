# P037: Skill End Exception Diagnostic Cleanup

Status: done
Parent: P020
Root: P000
Package: problems/P000/children/P004/children/P020/children/P037
Body: problems/P000/children/P004/children/P020/children/P037/README.md
Ticket(s): T034

## Problem
`context_skill_end` uses SQLite projection for normal empty/mismatch/success decisions, but its exception branch still falls back to `_collect_active_stack(...)` to build diagnostic response data. Exception diagnostics can become future authority if left as old file-walk residue.

This belongs under Phase 3D because `skill_end` is a core LIFO path and the remaining file-walk usage is isolated to its failure/diagnostic branch.

## Success Criteria
- `skill_end` exception responses use the projection frames captured at function entry, or a clearly non-authoritative empty diagnostic if projection read itself failed.
- `context_skill_end` contains no `_collect_active_stack(...)` calls.
- Existing `missing_scope_id`, `stack_empty`, `scope_mismatch`, and success API semantics are preserved.
- Tests cover an injected close failure and assert the error response reports projection-derived `actual_stack_top` / stack data without file-walk fallback.

## Subproblems
- none

## Results
- R031

## Latest Check
C033

## Bodies
- Problem: problems/P000/children/P004/children/P020/children/P037/README.md
- Ticket T034: problems/P000/children/P004/children/P020/children/P037/tickets/T034.md
- Result R031: problems/P000/children/P004/children/P020/children/P037/results/R031.md
- Check C033: problems/P000/children/P004/children/P020/children/P037/checks/C033.md

## Follow-ups
- none
