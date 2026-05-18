# P640: RW Scratch Cleanup Post-Scan Verification

Status: done
Parent: P636
Root: P000
Source Ticket: T632 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640/README.md
Ticket(s): T638

## Problem
After layout and fixture changes, verify no Cortex code/test still advertises root `/rw/scratch` as the default/canonical scratch path.

## Success Criteria
- Runs post-change scans for `/rw/scratch`, `RW_SCRATCH`, and `/rw/subagents`.
- Classifies any remaining root `/rw/scratch` hits as lower-layer/out-of-scope or follow-up-worthy.
- Runs focused Cortex/LogicalFS tests needed to prove cleanup did not break current behavior.

## Subproblems
- none

## Results
- R633

## Latest Check
C674

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640/README.md
- Ticket T638: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640/tickets/T638.md
- Result R633: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640/results/R633.md
- Check C674: problems/P000/children/P005/children/P554/children/P631/children/P636/children/P640/checks/C674.md

## Follow-ups
- none
