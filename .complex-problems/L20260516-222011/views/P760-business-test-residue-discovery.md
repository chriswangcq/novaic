# P760: Business test residue discovery

Status: done
Parent: P758
Root: P000
Source Ticket: T748 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760/README.md
Ticket(s): T750

## Problem
Scan `novaic-business` tests and test-like files for stale direct Queue/Gateway/Device wording, hidden fallback/compatibility residue, and misleading ownership assumptions. This belongs under P758 because Business tests may encode old dispatch or dependency-boundary expectations.

## Success Criteria
- Business test files are discovered with bounded commands.
- Suspicious Business test hits are classified as current guard fixture, intentional dispatch behavior, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.

## Subproblems
- none

## Results
- R740

## Latest Check
C785

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760/README.md
- Ticket T750: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760/tickets/T750.md
- Result R740: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760/results/R740.md
- Check C785: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P760/checks/C785.md

## Follow-ups
- none
