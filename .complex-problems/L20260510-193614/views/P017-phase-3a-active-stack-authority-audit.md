# P017: Phase 3A Active Stack Authority Audit

Status: done
Parent: P004
Root: P000
Package: problems/P000/children/P004/children/P017
Body: problems/P000/children/P004/children/P017/README.md
Ticket(s): T015

## Problem
Before changing runtime stack authority, identify every active-stack/status read and write path and classify whether it belongs to operational control state, semantic context projection, or trace/debug output. This prevents mixing the SQLite control stack with the existing context event projection stack.

## Success Criteria
- All `_collect_active_stack`, `context_status`, `skill_begin`, `skill_end`, finalize, and stack-projection call sites are cataloged.
- Each call site is classified as runtime authority, semantic context projection, trace/debug, or test-only.
- The next implementation tickets have explicit dependency boundaries and no ambiguous stack source remains unclassified.

## Subproblems
- none

## Results
- R013

## Latest Check
C014

## Bodies
- Problem: problems/P000/children/P004/children/P017/README.md
- Ticket T015: problems/P000/children/P004/children/P017/tickets/T015.md
- Result R013: problems/P000/children/P004/children/P017/results/R013.md
- Check C014: problems/P000/children/P004/children/P017/checks/C014.md

## Follow-ups
- none
