# P636: RW Scratch Layout Cleanup and Test Update

Status: done
Parent: P631
Root: P000
Source Ticket: T630 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P636
Body: problems/P000/children/P005/children/P554/children/P631/children/P636/README.md
Ticket(s): T632

## Problem
After inventory, remove root `/rw/scratch` as a default Workspace layout and update tests that encode the old global scratch convention, without breaking valid arbitrary `/rw` writes.

## Success Criteria
- Removes or updates high-confidence legacy root `/rw/scratch` initialization/contract references.
- Keeps generic `/rw` path behavior covered by tests using neutral or current subagent-aware paths.
- Preserves LogicalFS `RW_SCRATCH=/rw/subagents/{id}/scratch` behavior.
- Runs focused Cortex and LogicalFS tests.

## Subproblems
- P638: Workspace Default RW Layout Cleanup
- P639: Cortex RW Scratch Fixture Rewrite
- P640: RW Scratch Cleanup Post-Scan Verification

## Results
- R634

## Latest Check
C675

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P636/README.md
- Ticket T632: problems/P000/children/P005/children/P554/children/P631/children/P636/tickets/T632.md
- Result R634: problems/P000/children/P005/children/P554/children/P631/children/P636/results/R634.md
- Check C675: problems/P000/children/P005/children/P554/children/P631/children/P636/checks/C675.md

## Follow-ups
- none
