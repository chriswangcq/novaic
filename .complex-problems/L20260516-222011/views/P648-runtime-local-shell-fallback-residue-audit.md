# P648: Runtime Local Shell Fallback Residue Audit

Status: done
Parent: P632
Root: P000
Source Ticket: T642 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P632/children/P648
Body: problems/P000/children/P005/children/P554/children/P632/children/P648/README.md
Ticket(s): T645

## Problem
The runtime should use the intended LogicalFS/sandbox service path, not silently fall back to local shell execution or local filesystem materialization when service wiring is unavailable.

## Success Criteria
- Scans runtime/cortex/sandbox code for local shell fallback, direct subprocess/local execution fallback, `fallback`, `local`, and sandbox service bypass terms.
- Classifies remaining hits as intended error handling/test coverage or active hidden fallback.
- Removes or creates follow-up for any active hidden fallback that can run instead of failing loudly.

## Subproblems
- P651: Explicit Cortex API URL for Shell LogicalFS Environment

## Results
- R643

## Latest Check
C685

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P632/children/P648/README.md
- Ticket T645: problems/P000/children/P005/children/P554/children/P632/children/P648/tickets/T645.md
- Result R643: problems/P000/children/P005/children/P554/children/P632/children/P648/results/R643.md
- Check C685: problems/P000/children/P005/children/P554/children/P632/children/P648/checks/C685.md

## Follow-ups
- none
