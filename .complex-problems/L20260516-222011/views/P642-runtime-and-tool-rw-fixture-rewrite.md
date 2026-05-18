# P642: Runtime and Tool RW Fixture Rewrite

Status: done
Parent: P639
Root: P000
Source Ticket: T634 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642/README.md
Ticket(s): T636

## Problem
Runtime, metrics, hooks, chaos, and wave tests use `/rw/scratch` as generic writable fixtures. These should use current paths that match whether the file must be shell-visible or only Cortex-readable.

## Success Criteria
- Updates `test_runtime.py`, `test_cortex_chaos.py`, `test_hooks_limits.py`, `test_tool_metrics.py`, and `test_wave4_metrics.py` root scratch fixtures.
- Uses shell-visible current paths where shell/runtime behavior needs mounted files.
- Runs focused tests for touched files.

## Subproblems
- none

## Results
- R630

## Latest Check
C671

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642/README.md
- Ticket T636: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642/tickets/T636.md
- Result R630: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642/results/R630.md
- Check C671: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P639/children/P642/checks/C671.md

## Follow-ups
- none
