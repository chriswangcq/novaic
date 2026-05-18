# P644: Final RW Scratch Residue Scan Classification

Status: done
Parent: P637
Root: P000
Source Ticket: T639 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644
Body: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644/README.md
Ticket(s): T640

## Problem
The final guard needs a fresh scan that classifies every remaining root `/rw/scratch` occurrence after the cleanup chain, so stale production/default-contract residue cannot hide behind prior results.

## Success Criteria
- Runs and records fresh scans for `/rw/scratch`, `rw/scratch`, `RW_SCRATCH`, and `/rw/subagents` across Cortex and LogicalFS.
- Classifies every remaining root `/rw/scratch` hit as negative guard, lower-layer generic test, or follow-up-worthy residue.
- Confirms Cortex production code and positive test fixtures no longer advertise root `/rw/scratch` as default/canonical scratch.

## Subproblems
- none

## Results
- R635

## Latest Check
C676

## Bodies
- Problem: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644/README.md
- Ticket T640: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644/tickets/T640.md
- Result R635: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644/results/R635.md
- Check C676: problems/P000/children/P005/children/P554/children/P631/children/P637/children/P644/checks/C676.md

## Follow-ups
- none
