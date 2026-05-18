# P761: Device test residue discovery

Status: done
Parent: P758
Root: P000
Source Ticket: T748 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761/README.md
Ticket(s): T751

## Problem
Scan `novaic-device` tests and test-like files for stale inline screenshot/media routes, direct Gateway/Business ownership wording, base64/media residue, and fallback/compatibility assumptions. This belongs under P758 because Device tests can preserve removed media/control route expectations.

## Success Criteria
- Device test files are discovered with bounded commands.
- Suspicious Device test hits are classified as current hardware/protocol guard, intentional media fixture, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.

## Subproblems
- none

## Results
- R741

## Latest Check
C786

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761/README.md
- Ticket T751: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761/tickets/T751.md
- Result R741: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761/results/R741.md
- Check C786: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P761/checks/C786.md

## Follow-ups
- none
