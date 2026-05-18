# P554: LogicalFS Sandbox Blob Layering Remediation

Status: done
Parent: P005
Root: P000
Source Ticket: T549 (split)
Source Check: none
Package: problems/P000/children/P005/children/P554
Body: problems/P000/children/P005/children/P554/README.md
Ticket(s): T626

## Problem
Remove or tighten high-confidence stale fallback/backdoor paths found by the residue inventory. This child belongs under P005 because the user explicitly prefers physical cleanup over compatibility residue.

## Success Criteria
- High-confidence stale paths are removed or replaced with intended service boundaries.
- Ambiguous paths are not guessed; they are documented or split into follow-up problems.
- Changed code has focused tests or static guards.
- No local fallback is retained unless explicitly justified.

## Subproblems
- P630: Cortex Workspace Materialize API Removal
- P631: Legacy RW Scratch Layout Cleanup
- P632: LogicalFS Sandbox Fallback Remediation Guard

## Results
- R650

## Latest Check
C692

## Bodies
- Problem: problems/P000/children/P005/children/P554/README.md
- Ticket T626: problems/P000/children/P005/children/P554/tickets/T626.md
- Result R650: problems/P000/children/P005/children/P554/results/R650.md
- Check C692: problems/P000/children/P005/children/P554/checks/C692.md

## Follow-ups
- none
