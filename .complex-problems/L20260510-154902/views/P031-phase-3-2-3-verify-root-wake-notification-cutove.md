# P031: Phase 3.2.3: Verify root/wake/notification cutover boundaries

Status: done
Parent: P024
Root: P000
Package: problems/P000/children/P004/children/P024/children/P031
Body: problems/P000/children/P004/children/P024/children/P031/README.md
Ticket(s): T025

## Problem
After root/wake and notification events are wired, run a focused audit to ensure there is no hidden bypass for these facts and that later Phase 3 children still own unrelated context/tool/skill writes.

## Success Criteria
- Static scans identify all remaining direct writes related to root/wake/notification lifecycle and explain whether they are projection/debug-only or still pending.
- Focused tests for lifecycle and notification event writes pass.
- Full Cortex suite passes.
- Any remaining direct source-of-truth write becomes a follow-up before P024 closes.

## Subproblems
- none

## Results
- R022

## Latest Check
C024

## Bodies
- Problem: problems/P000/children/P004/children/P024/children/P031/README.md
- Ticket T025: problems/P000/children/P004/children/P024/children/P031/tickets/T025.md
- Result R022: problems/P000/children/P004/children/P024/children/P031/results/R022.md
- Check C024: problems/P000/children/P004/children/P024/children/P031/checks/C024.md

## Follow-ups
- none
