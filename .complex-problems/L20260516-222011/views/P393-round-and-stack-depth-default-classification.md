# P393: Round and stack-depth default classification

Status: done
Parent: P389
Root: P000
Source Ticket: T380 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393
Body: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393/README.md
Ticket(s): T388

## Problem
The widened guard also found stack depth and round number defaults in wake finalization and recovery paths. They are not session generation, but they are control-plane defaults and need conscious classification.

## Success Criteria
- Classify `stack_depth_at_finalize`, `round_num`, and retry/count defaults as safe or patch them with explicit validation where they affect control flow.
- Ensure wake finalize and recovery behavior remains covered by focused tests.
- Final matrix clearly separates session generation authority from harmless display/audit counters.

## Subproblems
- none

## Results
- R380

## Latest Check
C403

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393/README.md
- Ticket T388: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393/tickets/T388.md
- Result R380: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393/results/R380.md
- Check C403: problems/P000/children/P004/children/P278/children/P283/children/P328/children/P339/children/P380/children/P385/children/P388/children/P389/children/P393/checks/C403.md

## Follow-ups
- none
