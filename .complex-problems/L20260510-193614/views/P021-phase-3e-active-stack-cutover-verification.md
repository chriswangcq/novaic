# P021: Phase 3E Active Stack Cutover Verification

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P021
Body: problems/P000/children/P004/children/P021/README.md
Ticket(s): T037

## Problem
The active-stack/status cutover needs a final verification pass proving SQLite is authoritative and that old file-walk control paths are gone.

## Success Criteria
- Targeted tests cover nesting, mismatch, finalize/open-child behavior, restart recovery, and status reads.
- Static residue search proves runtime active-stack authority no longer depends on `_collect_active_stack` or equivalent file walking.
- Broader Cortex targeted tests and `py_compile` pass.
- Any remaining stack-related file projection code is documented as trace/repair/debug, not runtime authority.

## Subproblems
- P040: Delete Or Isolate Workspace Active Path File-Walk Helper

## Results
- R035

## Latest Check
C039

## Bodies
- Problem: problems/P000/children/P004/children/P021/README.md
- Ticket T037: problems/P000/children/P004/children/P021/tickets/T037.md
- Result R035: problems/P000/children/P004/children/P021/results/R035.md
- Check C037: problems/P000/children/P004/children/P021/checks/C037.md
- Check C039: problems/P000/children/P004/children/P021/checks/C039.md

## Follow-ups
- P040: Delete Or Isolate Workspace Active Path File-Walk Helper
