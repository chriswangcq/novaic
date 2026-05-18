# P759: Gateway test residue discovery

Status: done
Parent: P758
Root: P000
Source Ticket: T748 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759/README.md
Ticket(s): T749

## Problem
Scan `novaic-gateway` tests and test-like files for stale Gateway ownership, direct business path, fallback/compatibility, and media/control residue. This belongs under P758 because Gateway test fixtures may preserve old route or ownership assumptions even when production Gateway code is clean.

## Success Criteria
- Gateway test files are discovered with bounded commands.
- Suspicious Gateway test hits are classified as current guard fixture, intentional HTTP edge behavior, stale residue, or unrelated vocabulary.
- Exact stale remediation candidates are listed, or absence is explicitly recorded.
- No product code is modified in this discovery child.

## Subproblems
- none

## Results
- R739

## Latest Check
C784

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759/README.md
- Ticket T749: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759/tickets/T749.md
- Result R739: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759/results/R739.md
- Check C784: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P753/children/P756/children/P758/children/P759/checks/C784.md

## Follow-ups
- none
